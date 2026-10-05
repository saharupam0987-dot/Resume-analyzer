import io
import pytest
from pathlib import Path
from api.models import TaskJob

TEST_PDF_PATH = Path(__file__).resolve().parent.parent / "test_course_material.pdf"


def test_create_task_unauthorized(client):
    """Anonymous or non-teacher user cannot upload and trigger background tasks."""
    response = client.post(
        "/exams/process-pdf",
        files={"pdf_file": ("test.pdf", b"%PDF-1.4 dummy", "application/pdf")},
    )
    assert response.status_code == 401


def test_create_task_invalid_file_type(client, teacher_auth_headers):
    """Uploading a non-PDF file returns 400 Bad Request."""
    response = client.post(
        "/exams/process-pdf",
        headers=teacher_auth_headers,
        files={"pdf_file": ("notes.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    assert "only pdf" in response.json()["detail"].lower()


def test_create_task_success(client, teacher_auth_headers):
    """Test 2: Task creation returns task_id immediately with QUEUED status."""
    with open(TEST_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    response = client.post(
        "/exams/process-pdf",
        headers=teacher_auth_headers,
        files={"pdf_file": ("test_course_material.pdf", pdf_bytes, "application/pdf")},
        data={"collection_name": "test_collection_api"},
    )

    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["task_id"] > 0
    assert data["status"] in ("QUEUED", "COMPLETED")  # Eager execution might complete immediately
    assert "task" in data["message"].lower() or "queued" in data["message"].lower()


def test_get_task_status_endpoint(client, db_session):
    """Test 5: GET /tasks/{task_id} returns accurate task progress and metadata."""
    job = TaskJob(
        task_type="full_pdf_pipeline",
        status="PROCESSING",
        progress=65,
        message="Generating embeddings...",
        result_metadata={"test": "data"},
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    response = client.get(f"/tasks/{job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == job.id
    assert data["status"] == "PROCESSING"
    assert data["progress"] == 65
    assert data["message"] == "Generating embeddings..."


def test_get_task_status_not_found(client):
    """Non-existent task returns 404 Not Found."""
    response = client.get("/tasks/9999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_task_status_by_celery_uuid(client, db_session):
    """GET /tasks/{task_id} can look up by Celery task UUID."""
    uuid_str = "celery-uuid-12345-abcde"
    job = TaskJob(
        celery_task_id=uuid_str,
        task_type="pdf_processing",
        status="COMPLETED",
        progress=100,
        message="PDF text extracted successfully",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    response = client.get(f"/tasks/{uuid_str}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == job.id
    assert data["celery_task_id"] == uuid_str
    assert data["status"] == "COMPLETED"
    assert data["progress"] == 100
