from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.database import get_db
from api.models import TaskJob
from api.schemas import TaskStatusResponse
from tasks.celery_app import celery_app
from celery.result import AsyncResult

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Fetch the status and progress of a background processing task.
    Accepts either the integer database TaskJob ID or the Celery task UUID.
    """
    job = None
    if task_id.isdigit():
        job = db.query(TaskJob).filter(TaskJob.id == int(task_id)).first()

    if not job:
        job = db.query(TaskJob).filter(TaskJob.celery_task_id == task_id).first()

    if not job:
        # Check Celery directly if known by Celery
        try:
            res = AsyncResult(task_id, app=celery_app)
            if res and res.state and res.state != "PENDING":
                status_map = {
                    "PENDING": "QUEUED",
                    "STARTED": "PROCESSING",
                    "SUCCESS": "COMPLETED",
                    "FAILURE": "FAILED",
                    "RETRY": "PROCESSING",
                }
                return TaskStatusResponse(
                    task_id=0,
                    celery_task_id=task_id,
                    task_type="celery_task",
                    status=status_map.get(res.state, res.state),
                    progress=100 if res.state == "SUCCESS" else 50,
                    message=f"Celery task in state: {res.state}",
                    error=str(res.result) if res.state == "FAILURE" else None,
                )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id '{task_id}' not found",
        )

    return TaskStatusResponse(
        task_id=job.id,
        celery_task_id=job.celery_task_id,
        task_type=job.task_type,
        status=job.status,
        progress=job.progress,
        message=job.message or "",
        error=job.error,
        result_metadata=job.result_metadata or {},
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
