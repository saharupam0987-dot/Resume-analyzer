from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks for embedding.

    Args:
        text: The full text to split.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of text chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return chunks


def chunk_documents(documents: dict[str, str]) -> list[dict]:
    """Chunk multiple documents, preserving source metadata.

    Args:
        documents: Dict mapping filename to text.

    Returns:
        List of dicts with 'text', 'source', and 'chunk_index' keys.
    """
    all_chunks = []
    for source, text in documents.items():
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": source,
                "chunk_index": i,
            })
    return all_chunks
