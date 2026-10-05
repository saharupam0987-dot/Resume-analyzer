from rag.vector_store import query_collection


def retrieve_context(collection_name: str, topic: str, n_results: int = 8) -> str:
    """Retrieve relevant context for a topic from the vector store.

    Args:
        collection_name: The ChromaDB collection to search.
        topic: The topic to search for.
        n_results: How many chunks to retrieve.

    Returns:
        Concatenated relevant text chunks.
    """
    results = query_collection(collection_name, topic, n_results=n_results)
    if not results:
        return ""

    context_parts = []
    for r in results:
        context_parts.append(r["text"])

    return "\n\n---\n\n".join(context_parts)


def retrieve_context_for_topics(collection_name: str, topics: list[str],
                                 results_per_topic: int = 6) -> dict[str, str]:
    """Retrieve context for multiple topics.

    Args:
        collection_name: The ChromaDB collection.
        topics: List of topic names.
        results_per_topic: Chunks per topic.

    Returns:
        Dict mapping topic name to retrieved context.
    """
    topic_contexts = {}
    for topic in topics:
        # For the auto-filled "General" topic, use a broad query
        query = "key concepts definitions and important topics" if topic == "General" else topic
        context = retrieve_context(collection_name, query, n_results=results_per_topic)
        topic_contexts[topic] = context
    return topic_contexts
