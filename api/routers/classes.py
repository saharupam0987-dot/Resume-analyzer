from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.database import get_db
from api.models import ClassRoom, Enrollment, Student, Exam, ExamAssignment, Teacher
from api.schemas import (
    ClassCreate,
    ClassOut,
    StudentOut,
    EnrollmentOut,
    ExamOut,
)
from api.security import get_current_user
from api.routers.exams import clean_exam_options

router = APIRouter(tags=["Classrooms"])


# ============================================================
# Helper Functions
# ============================================================

def _build_class_out(classroom: ClassRoom) -> ClassOut:
    return ClassOut(
        id=classroom.id,
        name=classroom.name,
        description=classroom.description or "",
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        student_count=len(classroom.enrollments) if classroom.enrollments else 0,
        exam_count=len(classroom.assignments) if classroom.assignments else 0,
    )


# ============================================================
# 3. TEACHER CLASS APIs
# ============================================================

@router.post("/classes", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(
    data: ClassCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new classroom. Logged-in teacher automatically becomes the owner."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create classrooms",
        )

    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classroom name cannot be empty",
        )

    classroom = ClassRoom(
        name=name,
        description=(data.description or "").strip(),
        teacher_id=current_user["id"],
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return _build_class_out(classroom)


@router.get("/classes", response_model=List[ClassOut])
def list_teacher_classes(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return ONLY classrooms belonging to the logged-in teacher."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can list teacher classrooms",
        )

    classes = (
        db.query(ClassRoom)
        .filter(ClassRoom.teacher_id == current_user["id"])
        .order_by(ClassRoom.id.desc())
        .all()
    )
    return [_build_class_out(c) for c in classes]


@router.get("/classes/available-students", response_model=List[StudentOut])
@router.get("/students", response_model=List[StudentOut])
def list_available_students(
    q: Optional[str] = Query(None, description="Search term for student name, email, or roll number"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Teacher endpoint to discover registered students for class enrollment."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view student directory",
        )

    query = db.query(Student)
    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (Student.name.ilike(search_pattern))
            | (Student.email.ilike(search_pattern))
            | (Student.roll_number.ilike(search_pattern))
        )

    students = query.order_by(Student.name.asc()).all()
    return students


@router.get("/classes/{class_id}", response_model=ClassOut)
def get_class_details(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return classroom only if the logged-in teacher owns it."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view classroom details",
        )

    classroom = (
        db.query(ClassRoom)
        .filter(ClassRoom.id == class_id, ClassRoom.teacher_id == current_user["id"])
        .first()
    )
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you do not have permission to view it",
        )

    return _build_class_out(classroom)


@router.delete("/classes/{class_id}")
def delete_class(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allow deletion only if the logged-in teacher owns the class."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can delete classrooms",
        )

    classroom = (
        db.query(ClassRoom)
        .filter(ClassRoom.id == class_id, ClassRoom.teacher_id == current_user["id"])
        .first()
    )
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you do not have permission to delete it",
        )

    db.delete(classroom)
    db.commit()
    return {"message": "Classroom deleted successfully"}


# ============================================================
# 4. STUDENT ENROLLMENT MANAGEMENT (Teacher Only)
# ============================================================

@router.post(
    "/classes/{class_id}/students/{student_id}",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
)
def enroll_student(
    class_id: int,
    student_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll a student into a class. Enforces teacher ownership and prevents duplicate enrollment."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can enroll students into classrooms",
        )

    classroom = (
        db.query(ClassRoom)
        .filter(ClassRoom.id == class_id, ClassRoom.teacher_id == current_user["id"])
        .first()
    )
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you do not own it",
        )

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    existing_enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.class_id == class_id, Enrollment.student_id == student_id)
        .first()
    )
    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this class",
        )

    enrollment = Enrollment(class_id=class_id, student_id=student_id)
    db.add(enrollment)
    try:
        db.commit()
        db.refresh(enrollment)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled in this class",
        )

    return enrollment


@router.delete("/classes/{class_id}/students/{student_id}")
def remove_student_from_class(
    class_id: int,
    student_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a student from the class. Only the owner teacher can remove students."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can remove students from classrooms",
        )

    classroom = (
        db.query(ClassRoom)
        .filter(ClassRoom.id == class_id, ClassRoom.teacher_id == current_user["id"])
        .first()
    )
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you do not own it",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(Enrollment.class_id == class_id, Enrollment.student_id == student_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in this class",
        )

    db.delete(enrollment)
    db.commit()
    return {"message": "Student removed from class successfully"}


@router.get("/classes/{class_id}/students", response_model=List[StudentOut])
def get_enrolled_students(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return ONLY students enrolled in that teacher's class."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view classroom student rosters",
        )

    classroom = (
        db.query(ClassRoom)
        .filter(ClassRoom.id == class_id, ClassRoom.teacher_id == current_user["id"])
        .first()
    )
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found or you do not own it",
        )

    students = (
        db.query(Student)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .filter(Enrollment.class_id == class_id)
        .order_by(Student.name.asc())
        .all()
    )
    return students


# ============================================================
# 5. STUDENT CLASS APIs
# ============================================================

@router.get("/student/classes", response_model=List[ClassOut])
def get_student_classes(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all classes the logged-in student belongs to. Students cannot see other classes."""
    if current_user.get("role") != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their enrolled classes",
        )

    classes = (
        db.query(ClassRoom)
        .join(Enrollment, Enrollment.class_id == ClassRoom.id)
        .filter(Enrollment.student_id == current_user["id"])
        .order_by(ClassRoom.name.asc())
        .all()
    )
    return [_build_class_out(c) for c in classes]


# ============================================================
# 12. CLASS → EXAM VIEW
# ============================================================

@router.get("/classes/{class_id}/exams", response_model=List[ExamOut])
def get_class_exams(
    class_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get exams assigned to a class.
    - For teachers: Only the class owner can access it.
    - For students: Only if they are enrolled in that class, and only active assignments.
    """
    user_role = current_user.get("role")
    user_id = current_user.get("id")

    if user_role == "teacher":
        classroom = (
            db.query(ClassRoom)
            .filter(ClassRoom.id == class_id, ClassRoom.teacher_id == user_id)
            .first()
        )
        if not classroom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Classroom not found or you do not own it",
            )

        exams = (
            db.query(Exam)
            .join(ExamAssignment, ExamAssignment.exam_id == Exam.id)
            .filter(ExamAssignment.class_id == class_id)
            .order_by(Exam.id.desc())
            .all()
        )
    elif user_role == "student":
        # Check enrollment
        enrollment = (
            db.query(Enrollment)
            .filter(Enrollment.class_id == class_id, Enrollment.student_id == user_id)
            .first()
        )
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this classroom",
            )

        exams = (
            db.query(Exam)
            .join(ExamAssignment, ExamAssignment.exam_id == Exam.id)
            .filter(ExamAssignment.class_id == class_id, ExamAssignment.is_active == True)
            .order_by(Exam.id.desc())
            .all()
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized role",
        )

    for exam in exams:
        clean_exam_options(exam)
    return exams
