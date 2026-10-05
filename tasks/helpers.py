import logging
from datetime import datetime
from typing import Optional, Dict, Any
from api.database import get_task_db_session
from api.models import TaskJob

logger = logging.getLogger("eval_app.tasks")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def update_job_status(
    task_job_id: int,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    result_metadata: Optional[Dict[str, Any]] = None,
    celery_task_id: Optional[str] = None,
) -> Optional[TaskJob]:
    """Safely updates a TaskJob record inside an isolated, worker-scoped DB session."""
    try:
        with get_task_db_session() as db:
            job = db.query(TaskJob).filter(TaskJob.id == task_job_id).first()
            if not job:
                logger.warning(f"TaskJob id={task_job_id} not found in database")
                return None

            if celery_task_id and not job.celery_task_id:
                job.celery_task_id = celery_task_id

            if status:
                job.status = status
                if status == "PROCESSING" and not job.started_at:
                    job.started_at = datetime.utcnow()
                elif status in ("COMPLETED", "FAILED"):
                    job.completed_at = datetime.utcnow()

            if progress is not None:
                job.progress = max(0, min(100, progress))

            if message is not None:
                job.message = message

            if error is not None:
                job.error = error

            if result_metadata is not None:
                current_meta = dict(job.result_metadata or {})
                current_meta.update(result_metadata)
                job.result_metadata = current_meta

            return job
    except Exception as e:
        logger.error(f"Failed to update TaskJob id={task_job_id}: {e}", exc_info=True)
        return None
