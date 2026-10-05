import os
import shutil
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import Exam, Question, TaskJob, ClassRoom, Enrollment, ExamAssignment
from api.schemas import (
    ExamOut, TaskCreateResponse, ExamAssignmentCreate, ExamAssignmentOut,
    ParseRequirementsRequest, ParseRequirementsResponse,
)
from api.security import get_current_user
from pdf_processing.extractor import extract_text_from_pdf
from generation.gemini_generator import generate_exam_from_text
from generation.requirement_parser import parse_exam_requirements
from storage.local import default_storage
from tasks.pdf_tasks import extract_pdf_task
from tasks.embedding_tasks import process_pdf_and_embed_pipeline_task
from tasks.exam_tasks import generate_ai_exam_task

router = APIRouter(prefix="/exams", tags=["Exams"])
student_exams_router = APIRouter(prefix="/student", tags=["Student"])


def clean_exam_options(exam: Exam):
    """Ensures options is always a valid Python list so JSON serialization never fails."""
    if hasattr(exam, "questions") and exam.questions:
        for q in exam.questions:
            if isinstance(q.options, str):
                try:
                    q.options = json.loads(q.options)
                except Exception:
                    q.options = []
            elif q.options is None:
                q.options = []
    return exam


@router.post("/process-pdf", response_model=TaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
@router.post("/upload-pdf", response_model=TaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_and_process_pdf_async(
    pdf_file: UploadFile = File(...),
    collection_name: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Asynchronous PDF processing and vector store embedding endpoint.
    Saves PDF to persistent storage, creates a TaskJob, and dispatches Celery pipeline.
    Returns task_id immediately without blocking the HTTP request lifecycle.
    """
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can upload and process exam materials")

    filename = pdf_file.filename or "uploaded_document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported")

    # Read and persist file via storage abstraction
    file_bytes = await pdf_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    stored_file_path = default_storage.save_file(file_bytes, filename)

    if not collection_name or not collection_name.strip():
        collection_name = f"exam_{uuid.uuid4().hex[:12]}"

    # Create tracked task record in database
    job = TaskJob(
        task_type="full_pdf_pipeline",
        status="QUEUED",
        progress=0,
        message="PDF processing and embedding task queued",
        result_metadata={"original_filename": filename, "collection_name": collection_name},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to Celery worker
    try:
        async_task = process_pdf_and_embed_pipeline_task.delay(
            task_job_id=job.id,
            file_path=stored_file_path,
            collection_name=collection_name,
            source_name=filename,
        )
        job.celery_task_id = async_task.id
        db.commit()
    except Exception as e:
        job.status = "FAILED"
        job.error = "Failed to dispatch task to message broker. Ensure Redis is running."
        db.commit()
        raise HTTPException(status_code=503, detail="Message broker unavailable. Task could not be queued.")

    return TaskCreateResponse(
        task_id=job.id,
        celery_task_id=job.celery_task_id,
        status="QUEUED",
        message="PDF background processing started. Poll /tasks/{task_id} for progress.",
    )


@router.post("/extract-pdf", response_model=TaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def extract_pdf_async(
    pdf_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Asynchronous PDF text extraction task endpoint."""
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can extract exam documents")

    filename = pdf_file.filename or "uploaded_document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported")

    file_bytes = await pdf_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    stored_file_path = default_storage.save_file(file_bytes, filename)

    job = TaskJob(
        task_type="pdf_processing",
        status="QUEUED",
        progress=0,
        message="PDF extraction task queued",
        result_metadata={"original_filename": filename},
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        async_task = extract_pdf_task.delay(
            task_job_id=job.id,
            file_path=stored_file_path,
        )
        job.celery_task_id = async_task.id
        db.commit()
    except Exception:
        job.status = "FAILED"
        job.error = "Failed to dispatch task to message broker. Ensure Redis is running."
        db.commit()
        raise HTTPException(status_code=503, detail="Message broker unavailable. Task could not be queued.")

    return TaskCreateResponse(
        task_id=job.id,
        celery_task_id=job.celery_task_id,
        status="QUEUED",
        message="PDF extraction queued. Poll /tasks/{task_id} for progress.",
    )


# ============================================================
# NATURAL LANGUAGE EXAM REQUIREMENTS (PHASE 1)
# ============================================================

@router.post("/requirements/parse", response_model=ParseRequirementsResponse, status_code=status.HTTP_200_OK)
def parse_requirements_endpoint(
    data: ParseRequirementsRequest,
    current_user: dict = Depends(get_current_user),
):
    """Parses natural-language exam requirements into a structured Exam Blueprint.
    Only accessible to authenticated teachers.
    """
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can parse exam requirements",
        )

    if not data.requirements or not data.requirements.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requirements text cannot be empty",
        )

    return parse_exam_requirements(
        requirements=data.requirements,
        subject=data.subject,
        total_marks=data.total_marks,
        duration_minutes=data.duration_minutes,
    )


@router.post("/generate-ai", response_model=TaskCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_ai_exam(
    title: str = Form("AI Generated Exam"),
    total_marks: float = Form(50.0),
    num_mcq: int = Form(3),
    num_fill_blanks: int = Form(2),
    num_subjective: int = Form(2),
    strictness: str = Form("medium"),
    blueprint: Optional[str] = Form(None),
    pdf_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Asynchronous AI exam generation endpoint.
    Saves PDF, creates a TaskJob, and dispatches Celery generate_ai_exam_task.
    Supports structured blueprint from natural-language parsing if provided.
    Returns 202 with task_id immediately.
    """
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can generate exams")

    filename = pdf_file.filename or "uploaded_document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported")

    file_bytes = await pdf_file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    stored_file_path = default_storage.save_file(file_bytes, filename)

    parsed_blueprint = None
    if blueprint:
        try:
            parsed_blueprint = json.loads(blueprint) if isinstance(blueprint, str) else blueprint
        except Exception as parse_err:
            logger.warning("Could not deserialize blueprint JSON: %s", parse_err)
            parsed_blueprint = None

    metadata = {
        "original_filename": filename,
        "title": title,
    }
    if parsed_blueprint:
        metadata["has_blueprint"] = True
        metadata["blueprint_summary"] = {
            "questions": len(parsed_blueprint.get("question_requirements", [])),
            "difficulty": parsed_blueprint.get("global_requirements", {}).get("difficulty", strictness),
        }

    job = TaskJob(
        task_type="ai_exam_generation",
        status="QUEUED",
        progress=0,
        message="AI exam generation task queued",
        result_metadata=metadata,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        async_task = generate_ai_exam_task.delay(
            task_job_id=job.id,
            teacher_id=current_user["id"],
            title=title,
            total_marks=total_marks,
            num_mcq=num_mcq,
            num_fill_blanks=num_fill_blanks,
            num_subjective=num_subjective,
            strictness=strictness,
            file_path=stored_file_path,
            source_filename=filename,
            blueprint=parsed_blueprint,
        )
        job.celery_task_id = async_task.id
        db.commit()
    except Exception as e:
        job.status = "FAILED"
        job.error = "Failed to dispatch task to message broker. Ensure Redis is running."
        db.commit()
        raise HTTPException(status_code=503, detail="Message broker unavailable. Task could not be queued.")

    return TaskCreateResponse(
        task_id=job.id,
        celery_task_id=job.celery_task_id,
        status="QUEUED",
        message="AI exam generation queued. Poll /tasks/{task_id} for progress.",
    )



# ============================================================
# 7. EXAM ASSIGNMENT (Teacher Only)
# ============================================================

@router.post("/{exam_id}/assign/{class_id}", response_model=ExamAssignmentOut, status_code=status.HTTP_201_CREATED)
def assign_exam_to_class(
    exam_id: int,
    class_id: int,
    data: Optional[ExamAssignmentCreate] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Assign an exam to a classroom. Teacher must own both exam and classroom."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can assign exams to classrooms",
        )

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or exam.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or you do not own it",
        )

    classroom = db.query(ClassRoom).filter(ClassRoom.id == class_id).first()
    if not classroom or classroom.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you do not own it",
        )

    existing = (
        db.query(ExamAssignment)
        .filter(ExamAssignment.exam_id == exam_id, ExamAssignment.class_id == class_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Exam is already assigned to this classroom",
        )

    assignment = ExamAssignment(
        exam_id=exam_id,
        class_id=class_id,
        due_date=data.due_date if data else None,
        is_active=data.is_active if (data and data.is_active is not None) else True,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return ExamAssignmentOut(
        id=assignment.id,
        exam_id=assignment.exam_id,
        class_id=assignment.class_id,
        assigned_at=assignment.assigned_at,
        due_date=assignment.due_date,
        is_active=assignment.is_active,
        class_name=classroom.name,
        exam_title=exam.title,
    )


@router.delete("/{exam_id}/assign/{class_id}")
def unassign_exam_from_class(
    exam_id: int,
    class_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove exam assignment from a class. Only the owner teacher can remove it."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can unassign exams",
        )

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or exam.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or you do not own it",
        )

    assignment = (
        db.query(ExamAssignment)
        .filter(ExamAssignment.exam_id == exam_id, ExamAssignment.class_id == class_id)
        .first()
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam assignment not found",
        )

    db.delete(assignment)
    db.commit()
    return {"message": "Exam unassigned successfully"}


@router.get("/{exam_id}/assignments", response_model=List[ExamAssignmentOut])
def get_exam_assignments(
    exam_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return classrooms this exam has been assigned to. Only exam owner can access."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view exam assignments",
        )

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or exam.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or you do not own it",
        )

    assignments = (
        db.query(ExamAssignment)
        .filter(ExamAssignment.exam_id == exam_id)
        .order_by(ExamAssignment.id.desc())
        .all()
    )

    results = []
    for a in assignments:
        results.append(
            ExamAssignmentOut(
                id=a.id,
                exam_id=a.exam_id,
                class_id=a.class_id,
                assigned_at=a.assigned_at,
                due_date=a.due_date,
                is_active=a.is_active,
                class_name=a.classroom.name if a.classroom else None,
                exam_title=exam.title,
            )
        )
    return results


# ============================================================
# 8. STUDENT EXAM ACCESS CONTROL
# ============================================================

@student_exams_router.get("/exams", response_model=List[ExamOut])
def get_student_assigned_exams(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return ONLY active exams assigned to classes in which the student is enrolled."""
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access student exams",
        )

    exams = (
        db.query(Exam)
        .join(ExamAssignment, ExamAssignment.exam_id == Exam.id)
        .join(Enrollment, Enrollment.class_id == ExamAssignment.class_id)
        .filter(
            Enrollment.student_id == current_user["id"],
            ExamAssignment.is_active == True,
        )
        .distinct()
        .order_by(Exam.id.desc())
        .all()
    )
    for exam in exams:
        clean_exam_options(exam)
    return exams


@router.get("/student/exams", response_model=List[ExamOut])
def get_student_assigned_exams_alias(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Alias for GET /student/exams within the /exams prefix."""
    return get_student_assigned_exams(current_user=current_user, db=db)


# ============================================================
# 6. EXAM OWNERSHIP & GENERAL EXAM ACCESS
# ============================================================

@router.get("", response_model=List[ExamOut])
@router.get("/", response_model=List[ExamOut])
def list_exams(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Role-aware exam listing:
    - Teacher: Returns ONLY exams owned by the teacher.
    - Student: Returns ONLY active exams assigned to classes they are enrolled in.
    """
    role = current_user.get("role")
    user_id = current_user.get("id")

    if role == "teacher":
        exams = db.query(Exam).filter(Exam.teacher_id == user_id).order_by(Exam.id.desc()).all()
    elif role == "student":
        exams = (
            db.query(Exam)
            .join(ExamAssignment, ExamAssignment.exam_id == Exam.id)
            .join(Enrollment, Enrollment.class_id == ExamAssignment.class_id)
            .filter(
                Enrollment.student_id == user_id,
                ExamAssignment.is_active == True,
            )
            .distinct()
            .order_by(Exam.id.desc())
            .all()
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")

    for exam in exams:
        clean_exam_options(exam)
    return exams


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Role-based direct exam access verification:
    - Teacher: Must be the owner of the exam.
    - Student: Must be enrolled in at least one class that has an active assignment for this exam.
    If unauthorized: Returns 404 to avoid leaking private exam existence.
    """
    role = current_user.get("role")
    user_id = current_user.get("id")

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")

    if role == "teacher":
        if exam.teacher_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    elif role == "student":
        has_access = (
            db.query(ExamAssignment)
            .join(Enrollment, Enrollment.class_id == ExamAssignment.class_id)
            .filter(
                ExamAssignment.exam_id == exam_id,
                ExamAssignment.is_active == True,
                Enrollment.student_id == user_id,
            )
            .first()
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exam not found or not assigned to your classes",
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")

    return clean_exam_options(exam)


@router.delete("/{exam_id}")
def delete_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an exam. Allowed only if current user is a teacher and owns the exam."""
    if current_user.get("role") != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can delete exams")

    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or exam.teacher_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found or you do not own it",
        )

    db.delete(exam)
    db.commit()
    return {"message": "Exam deleted successfully"}