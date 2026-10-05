import os
import time
import logging
from tasks.celery_app import celery_app
from tasks.helpers import update_job_status
from pdf_processing.extractor import extract_text_from_pdf

logger = logging.getLogger("eval_app.tasks.pdf")


@celery_app.task(bind=True, name="tasks.pdf_tasks.extract_pdf_task")
def extract_pdf_task(self, task_job_id: int, file_path: str, max_pages: int = 100) -> dict:
    """Celery task to extract text from an uploaded PDF document.

    Args:
        task_job_id: The ID of the database TaskJob tracking this operation.
        file_path: Absolute or relative path to the PDF on disk.
        max_pages: Maximum number of pages to parse.

    Returns:
        Dictionary containing extraction summary and extracted text.
    """
    start_time = time.time()
    celery_task_id = self.request.id
    logger.info(f"Starting PDF extraction task | task_job_id={task_job_id} | celery_id={celery_task_id} | file={file_path}")

    # Stage 1: Mark task as processing
    update_job_status(
        task_job_id=task_job_id,
        celery_task_id=celery_task_id,
        status="PROCESSING",
        progress=15,
        message="Validating PDF file...",
    )

    # Check file existence
    if not file_path or not os.path.exists(file_path):
        err_msg = f"PDF file not found: {os.path.basename(file_path) if file_path else 'Unknown'}"
        logger.error(f"{err_msg} | task_job_id={task_job_id}")
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="File not found",
            error=err_msg,
        )
        raise FileNotFoundError(err_msg)

    # Stage 2: Extract text
    update_job_status(
        task_job_id=task_job_id,
        progress=40,
        message="Extracting text from PDF...",
    )

    try:
        extracted_text = extract_text_from_pdf(file_path, max_pages=max_pages)
    except Exception as e:
        logger.error(f"PyMuPDF failed to extract text from {file_path}: {e}", exc_info=True)
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="PDF extraction failed",
            error="Failed to extract text from PDF. The file may be corrupt or encrypted.",
        )
        raise ValueError("Corrupted or unreadable PDF document")

    if not extracted_text or not extracted_text.strip():
        err_msg = "PDF contains no readable text or is image-only."
        logger.warning(f"{err_msg} | task_job_id={task_job_id}")
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="No text extracted",
            error=err_msg,
        )
        raise ValueError(err_msg)

    duration = round(time.time() - start_time, 2)
    char_count = len(extracted_text)
    word_count = len(extracted_text.split())

    logger.info(
        f"PDF extraction completed successfully | task_job_id={task_job_id} | "
        f"chars={char_count} | words={word_count} | duration={duration}s"
    )

    meta = {
        "character_count": char_count,
        "word_count": word_count,
        "duration_seconds": duration,
        "file_name": os.path.basename(file_path),
    }

    update_job_status(
        task_job_id=task_job_id,
        status="COMPLETED",
        progress=100,
        message="PDF text extracted successfully",
        result_metadata=meta,
    )

    return {
        "task_job_id": task_job_id,
        "status": "COMPLETED",
        "extracted_text": extracted_text,
        "metadata": meta,
    }
