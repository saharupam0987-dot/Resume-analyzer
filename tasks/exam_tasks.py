import json
import logging
import os
import time

from tasks.celery_app import celery_app
from tasks.helpers import update_job_status

from api.database import get_task_db_session
from api.models import Exam, Question

from pdf_processing.extractor import extract_text_from_pdf
from generation.gemini_generator import generate_exam_from_text

from storage.local import default_storage


logger = logging.getLogger("eval_app.tasks.exam")


@celery_app.task(
    bind=True,
    name="tasks.exam_tasks.generate_ai_exam_task",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=30,
)
def generate_ai_exam_task(
    self,
    task_job_id: int,
    teacher_id: int,
    title: str,
    total_marks: float,
    num_mcq: int,
    num_fill_blanks: int,
    num_subjective: int,
    strictness: str,
    file_path: str,
    source_filename: str,
    blueprint: dict = None,
) -> dict:

    celery_task_id = self.request.id
    start_time = time.time()

    logger.info(
        "Starting AI exam generation | task_job_id=%s | celery_task_id=%s",
        task_job_id,
        celery_task_id,
    )

    update_job_status(
        task_job_id,
        status="PROCESSING",
        progress=5,
        message="Starting AI exam generation...",
    )

    try:
        # ---------------------------------------------------------
        # 1. Validate PDF
        # ---------------------------------------------------------
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError(
                f"PDF file not found: {file_path}"
            )

        update_job_status(
            task_job_id,
            status="PROCESSING",
            progress=20,
            message="Extracting text from PDF...",
        )

        # ---------------------------------------------------------
        # 2. Extract PDF text
        # ---------------------------------------------------------
        extracted_text = extract_text_from_pdf(file_path)

        if not extracted_text or not extracted_text.strip():
            raise ValueError(
                "Could not extract text from the uploaded PDF."
            )

        logger.info(
            "PDF extraction completed | characters=%s",
            len(extracted_text),
        )

        update_job_status(
            task_job_id,
            status="PROCESSING",
            progress=40,
            message="Generating questions using AI...",
        )

        # ---------------------------------------------------------
        # 3. Generate questions using Gemini
        # ---------------------------------------------------------
        questions_data = generate_exam_from_text(
            context_text=extracted_text,
            title=title,
            num_mcq=num_mcq,
            num_fill=num_fill_blanks,
            num_sub=num_subjective,
            strictness=strictness,
            blueprint=blueprint,
        )

        if not questions_data:
            raise ValueError(
                "AI failed to generate questions."
            )

        logger.info(
            "AI generated %s questions",
            len(questions_data),
        )

        update_job_status(
            task_job_id,
            status="PROCESSING",
            progress=80,
            message="Saving generated exam...",
        )

        # ---------------------------------------------------------
        # 4. Save exam + questions
        # ---------------------------------------------------------
        with get_task_db_session() as db:

            exam = Exam(
                title=title,
                teacher_id=teacher_id,
                total_marks=total_marks,
                num_mcq=num_mcq,
                num_fill_blanks=num_fill_blanks,
                num_subjective=num_subjective,
                evaluation_strictness=strictness,
                collection_name=source_filename,
                blueprint=blueprint or {},
                requirements_text=(blueprint.get("raw_requirements", "") if isinstance(blueprint, dict) else ""),
            )

            db.add(exam)
            db.flush()

            for idx, q in enumerate(questions_data):

                options = q.get("options", [])

                if isinstance(options, str):
                    try:
                        options = json.loads(options)
                    except Exception:
                        options = []

                question = Question(
                    exam_id=exam.id,
                    question_text=q.get(
                        "question_text",
                        q.get("question", "")
                    ),
                    question_type=q.get(
                        "question_type",
                        q.get("type", "subjective")
                    ),
                    options=options,
                    correct_answer=q.get(
                        "correct_answer",
                        q.get("answer", "")
                    ),
                    marks=float(q.get("marks", 1.0)),
                    topic=q.get("topic", "General"),
                    difficulty=q.get("difficulty", strictness),
                    question_number=idx + 1,
                )

                db.add(question)

            db.flush()

            exam_id = exam.id

        # ---------------------------------------------------------
        # 5. Complete
        # ---------------------------------------------------------
        duration = round(time.time() - start_time, 2)

        metadata = {
            "exam_id": exam_id,
            "question_count": len(questions_data),
            "source_filename": source_filename,
            "duration_seconds": duration,
        }

        update_job_status(
            task_job_id,
            status="COMPLETED",
            progress=100,
            message="AI exam generated successfully.",
            result_metadata=metadata,
        )

        logger.info(
            "AI exam generation completed | exam_id=%s | duration=%ss",
            exam_id,
            duration,
        )

        return metadata

    except (FileNotFoundError, ValueError) as exc:

        logger.error(
            "AI exam generation failed: %s",
            exc,
        )

        update_job_status(
            task_job_id,
            status="FAILED",
            progress=0,
            message="AI exam generation failed.",
            error=str(exc),
        )

        raise

    except Exception as exc:

        logger.exception(
            "Unexpected error during AI exam generation"
        )

        update_job_status(
            task_job_id,
            status="FAILED",
            progress=0,
            message="AI exam generation failed unexpectedly.",
            error=str(exc),
        )

        raise

    finally:

        # Delete temporary PDF after processing
        try:
            if file_path:
                default_storage.delete_file(file_path)
        except Exception:
            logger.warning(
                "Could not delete temporary PDF: %s",
                file_path,
            )