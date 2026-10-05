import os
import pytest
from pathlib import Path
from tasks.celery_app import celery_app
from tasks.pdf_tasks import extract_pdf_task
from tasks.embedding_tasks import generate_embeddings_task, process_pdf_and_embed_pipeline_task
from api.models import TaskJob
from api.database import get_task_db_session

TEST_PDF_PATH = str(Path(__file__).resolve().parent.parent / "test_course_material.pdf")


def test_celery_configuration():
    """Test 1: Celery configuration is valid."""
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.timezone == "UTC"
    assert "json" in celery_app.conf.accept_content
    tasks = celery_app.tasks
    assert "tasks.pdf_tasks.extract_pdf_task" in tasks
    assert "tasks.embedding_tasks.generate_embeddings_task" in tasks
    assert "tasks.embedding_tasks.process_pdf_and_embed_pipeline_task" in tasks


def test_pdf_extraction_task_success(db_session):
    """Test 3: PDF extraction task succeeds on valid PDF file."""
    job = TaskJob(task_type="pdf_processing", status="QUEUED", progress=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    async_res = extract_pdf_task.apply(args=[job.id, TEST_PDF_PATH])
    result = async_res.get()

    assert result["status"] == "COMPLETED"
    assert "extracted_text" in result
    assert len(result["extracted_text"]) > 0

    # Refresh job from DB
    db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert job.progress == 100
    assert job.message == "PDF text extracted successfully"
    assert job.result_metadata["character_count"] > 0
    assert job.error is None
    assert job.started_at is not None
    assert job.completed_at is not None


def test_pdf_extraction_missing_file(db_session):
    """Test 9: Missing file marks task as FAILED and raises FileNotFoundError."""
    job = TaskJob(task_type="pdf_processing", status="QUEUED", progress=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    with pytest.raises(FileNotFoundError):
        extract_pdf_task.apply(args=[job.id, "non_existent_file_xyz.pdf"]).get()

    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.progress == 0
    assert "not found" in job.error.lower()


def test_pdf_extraction_invalid_pdf(tmp_path, db_session):
    """Test 8: Corrupted/invalid PDF file fails safely with descriptive message."""
    invalid_file = tmp_path / "corrupted.pdf"
    invalid_file.write_text("THIS IS NOT A VALID PDF CONTENT")

    job = TaskJob(task_type="pdf_processing", status="QUEUED", progress=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    with pytest.raises(ValueError):
        extract_pdf_task.apply(args=[job.id, str(invalid_file)]).get()

    db_session.refresh(job)
    assert job.status == "FAILED"
    assert job.progress == 0
    assert "failed" in job.message.lower() or "no text" in job.message.lower()
    assert job.error is not None


def test_embedding_task_success(db_session):
    """Test 4: Embedding generation and vector store insertion."""
    job = TaskJob(task_type="embedding_generation", status="QUEUED", progress=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    sample_text = (
        "Binary search is an efficient algorithm for finding an item from a sorted list of items. "
        "It works by repeatedly dividing in half the portion of the list that could contain the item."
    )
    col_name = f"test_col_{job.id}"

    async_res = generate_embeddings_task.apply(args=[job.id, sample_text, col_name, "test_source.txt"])
    result = async_res.get()

    assert result["status"] == "COMPLETED"
    assert result["metadata"]["chunk_count"] > 0
    assert result["metadata"]["collection_name"] == col_name

    db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert job.progress == 100
    assert job.result_metadata["chunk_count"] > 0


def test_embedding_task_empty_text(db_session):
    """Test 7: Failed task due to empty input text."""
    job = TaskJob(task_type="embedding_generation", status="QUEUED", progress=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    with pytest.raises(ValueError):
        generate_embeddings_task.apply(args=[job.id, "", "empty_test"]).get()

    db_session.refresh(job)
    assert job.status == "FAILED"
    assert "empty text" in job.message.lower()


def test_full_pipeline_task_success(db_session):
    """Test 6: Full pipeline (PDF -> Extract -> Chunk -> Embed -> ChromaDB)."""
    job = TaskJob(task_type="full_pdf_pipeline", status="QUEUED", progress=0)
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    col_name = f"test_pipeline_{job.id}"
    async_res = process_pdf_and_embed_pipeline_task.apply(
        args=[job.id, TEST_PDF_PATH, col_name, "test_course_material.pdf"]
    )
    result = async_res.get()

    assert result["status"] == "COMPLETED"
    assert result["metadata"]["chunk_count"] > 0

    db_session.refresh(job)
    assert job.status == "COMPLETED"
    assert job.progress == 100
    assert "completed successfully" in job.message.lower()
    assert job.result_metadata["collection_name"] == col_name


def test_database_rollback_and_session_safety(db_session):
    """Test 10: Database transaction safety and rollback on error."""
    test_id = 999999
    try:
        with get_task_db_session() as db:
            job = TaskJob(id=test_id, task_type="rollback_test", status="QUEUED")
            db.add(job)
            db.flush()
            raise RuntimeError("Forced simulation error")
    except RuntimeError:
        pass

    with get_task_db_session() as db:
        rolled_back_job = db.query(TaskJob).filter(TaskJob.id == test_id).first()
        assert rolled_back_job is None
