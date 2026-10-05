import os
import time
import logging
from tasks.celery_app import celery_app
from tasks.helpers import update_job_status
from pdf_processing.extractor import extract_text_from_pdf
from pdf_processing.chunker import chunk_text
from rag.vector_store import add_documents

logger = logging.getLogger("eval_app.tasks.embedding")


@celery_app.task(
    bind=True,
    name="tasks.embedding_tasks.generate_embeddings_task",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=30,
)
def generate_embeddings_task(
    self,
    task_job_id: int,
    text: str,
    collection_name: str,
    source_name: str = "document",
) -> dict:
    """Celery task to chunk text and generate/store vector embeddings in ChromaDB.

    Args:
        task_job_id: Database TaskJob ID.
        text: Extracted text content.
        collection_name: ChromaDB collection name.
        source_name: Reference source label.

    Returns:
        Summary dict containing chunk count and collection details.
    """
    start_time = time.time()
    celery_task_id = self.request.id
    logger.info(
        f"Starting embedding task | task_job_id={task_job_id} | celery_id={celery_task_id} | "
        f"collection={collection_name} | text_len={len(text) if text else 0}"
    )

    update_job_status(
        task_job_id=task_job_id,
        celery_task_id=celery_task_id,
        status="PROCESSING",
        progress=20,
        message="Preparing text for chunking...",
    )

    if not text or not text.strip():
        err_msg = "No text provided to generate embeddings."
        logger.error(f"{err_msg} | task_job_id={task_job_id}")
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="Empty text",
            error=err_msg,
        )
        raise ValueError(err_msg)

    # Stage 1: Chunking
    update_job_status(
        task_job_id=task_job_id,
        progress=45,
        message="Splitting text into semantically overlapping chunks...",
    )

    chunks = chunk_text(text)
    if not chunks:
        err_msg = "Chunking produced 0 chunks from text."
        logger.error(f"{err_msg} | task_job_id={task_job_id}")
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="Chunking failed",
            error=err_msg,
        )
        raise ValueError(err_msg)

    chunk_docs = [
        {"text": c, "source": source_name, "chunk_index": i}
        for i, c in enumerate(chunks)
    ]

    # Stage 2: Embeddings & Vector Store
    update_job_status(
        task_job_id=task_job_id,
        progress=70,
        message=f"Generating embeddings for {len(chunk_docs)} chunks and storing in ChromaDB...",
    )

    try:
        add_documents(collection_name, chunk_docs)
    except (ConnectionError, TimeoutError) as trans_err:
        logger.warning(
            f"Transient error storing embeddings (retry {self.request.retries}/{self.max_retries}): {trans_err}"
        )
        update_job_status(
            task_job_id=task_job_id,
            message=f"Transient storage error. Retrying ({self.request.retries + 1}/{self.max_retries})...",
        )
        raise trans_err
    except Exception as e:
        logger.error(f"Failed to generate/store embeddings: {e}", exc_info=True)
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="Embedding generation failed",
            error="Failed to generate embeddings and index into vector store.",
        )
        raise

    duration = round(time.time() - start_time, 2)
    logger.info(
        f"Embedding task completed | task_job_id={task_job_id} | "
        f"collection={collection_name} | chunks={len(chunks)} | duration={duration}s"
    )

    meta = {
        "collection_name": collection_name,
        "chunk_count": len(chunks),
        "source_name": source_name,
        "duration_seconds": duration,
    }

    update_job_status(
        task_job_id=task_job_id,
        status="COMPLETED",
        progress=100,
        message="Embeddings generated and indexed into vector database",
        result_metadata=meta,
    )

    return {
        "task_job_id": task_job_id,
        "status": "COMPLETED",
        "metadata": meta,
    }


@celery_app.task(
    bind=True,
    name="tasks.embedding_tasks.process_pdf_and_embed_pipeline_task",
    autoretry_for=(ConnectionError, TimeoutError),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=30,
)
def process_pdf_and_embed_pipeline_task(
    self,
    task_job_id: int,
    file_path: str,
    collection_name: str,
    source_name: str = "document.pdf",
    max_pages: int = 100,
) -> dict:
    """Full background pipeline:
    PDF Extraction -> Text Cleaning -> Chunking -> Embedding Generation -> ChromaDB Store.

    Non-transient failures (corrupt PDF, file missing) fail immediately without retries.
    Transient network/DB errors are retried with exponential backoff.
    """
    start_time = time.time()
    celery_task_id = self.request.id
    logger.info(
        f"Starting full PDF+embedding pipeline | task_job_id={task_job_id} | celery_id={celery_task_id} | "
        f"file={file_path} | collection={collection_name}"
    )

    # 1. Verification
    update_job_status(
        task_job_id=task_job_id,
        celery_task_id=celery_task_id,
        status="PROCESSING",
        progress=10,
        message="Verifying uploaded file...",
    )

    if not file_path or not os.path.exists(file_path):
        err_msg = f"PDF file not found at path: {file_path}"
        logger.error(f"{err_msg} | task_job_id={task_job_id}")
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="File not found",
            error=err_msg,
        )
        raise FileNotFoundError(err_msg)

    # 2. PDF Extraction
    update_job_status(
        task_job_id=task_job_id,
        progress=30,
        message="Extracting text from PDF...",
    )

    try:
        extracted_text = extract_text_from_pdf(file_path, max_pages=max_pages)
    except Exception as e:
        logger.error(f"PyMuPDF error: {e}", exc_info=True)
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

    # 3. Text cleaning & Chunking
    update_job_status(
        task_job_id=task_job_id,
        progress=55,
        message="Cleaning text and creating semantic chunks...",
    )

    # Clean whitespace while preserving structure
    cleaned_text = "\n".join(
        line.strip() for line in extracted_text.splitlines() if line.strip()
    )
    chunks = chunk_text(cleaned_text)

    if not chunks:
        err_msg = "Failed to create chunks from document."
        logger.error(f"{err_msg} | task_job_id={task_job_id}")
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="Chunking failed",
            error=err_msg,
        )
        raise ValueError(err_msg)

    chunk_docs = [
        {"text": c, "source": source_name, "chunk_index": i}
        for i, c in enumerate(chunks)
    ]

    # 4. Embeddings & ChromaDB Vector Store
    update_job_status(
        task_job_id=task_job_id,
        progress=80,
        message=f"Generating embeddings for {len(chunk_docs)} chunks and storing in ChromaDB...",
    )

    try:
        add_documents(collection_name, chunk_docs)
    except (ConnectionError, TimeoutError) as trans_err:
        logger.warning(f"Transient error storing embeddings: {trans_err}")
        update_job_status(
            task_job_id=task_job_id,
            message=f"Transient storage error. Retrying ({self.request.retries + 1}/{self.max_retries})...",
        )
        raise trans_err
    except Exception as e:
        logger.error(f"Failed to generate/store embeddings: {e}", exc_info=True)
        update_job_status(
            task_job_id=task_job_id,
            status="FAILED",
            progress=0,
            message="Embedding generation failed",
            error="Failed to store embeddings in vector database.",
        )
        raise

    duration = round(time.time() - start_time, 2)
    meta = {
        "file_name": source_name,
        "collection_name": collection_name,
        "character_count": len(extracted_text),
        "chunk_count": len(chunks),
        "duration_seconds": duration,
    }

    logger.info(
        f"Pipeline completed successfully | task_job_id={task_job_id} | "
        f"collection={collection_name} | chunks={len(chunks)} | duration={duration}s"
    )

    update_job_status(
        task_job_id=task_job_id,
        status="COMPLETED",
        progress=100,
        message="Document processing and knowledge base creation completed successfully",
        result_metadata=meta,
    )

    return {
        "task_job_id": task_job_id,
        "status": "COMPLETED",
        "metadata": meta,
    }
