import chromadb
from chromadb.config import Settings
from config.settings import CHROMA_PERSIST_DIR
from rag.embeddings import embed_texts
import os

_client = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the singleton ChromaDB client."""
    global _client
    if _client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def create_collection(collection_name: str) -> chromadb.Collection:
    """Create or get a ChromaDB collection."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def add_documents(collection_name: str, chunks: list[dict]):
    """Add document chunks to a ChromaDB collection.

    Args:
        collection_name: Name of the collection.
        chunks: List of dicts with 'text', 'source', 'chunk_index' keys.
    """
    collection = create_collection(collection_name)

    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    ids = [f"{c['source']}_{c['chunk_index']}" for c in chunks]
    metadatas = [{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks]

    # ChromaDB has a batch limit, process in batches of 100
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        end = min(i + batch_size, len(texts))
        collection.add(
            documents=texts[i:end],
            embeddings=embeddings[i:end],
            ids=ids[i:end],
            metadatas=metadatas[i:end],
        )


def query_collection(collection_name: str, query_text: str, n_results: int = 5) -> list[dict]:
    """Query a collection for relevant documents.

    Args:
        collection_name: Name of the collection to query.
        query_text: The query text.
        n_results: Number of results to return.

    Returns:
        List of dicts with 'text', 'source', 'score' keys.
    """
    collection = create_collection(collection_name)
    query_embedding = embed_texts([query_text])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "text": doc,
                "source": results["metadatas"][0][i]["source"],
                "score": 1 - results["distances"][0][i],  # cosine distance to similarity
            })

    return output


def delete_collection(collection_name: str):
    """Delete a ChromaDB collection."""
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
    except ValueError:
        pass
