"""
Main RAG wrapper - the interface Grok uses for persistent memory.
"""

from pinecone_client import query_similar, upsert_document
from embeddings import generate_embedding
from typing import Optional


def recall_memory(
    query: str,
    top_k: int = 5,
    sphere_filter: Optional[str] = None
) -> str:
    """
    Recall relevant memories for a given query.
    This is the main function Grok should call.
    
    Args:
        query: The question or topic to recall context for
        top_k: Number of relevant memories to retrieve
        sphere_filter: Optional sphere to limit search (e.g., "S069")
    
    Returns:
        Formatted string of relevant memories for injection into prompt
    """
    results = query_similar(
        query=query,
        top_k=top_k,
        sphere_filter=sphere_filter
    )
    
    if not results:
        return "[No relevant memories found]"
    
    # Format for prompt injection
    memory_text = "=== ARCHIVAL MEMORY (RAG RETRIEVAL) ===\n\n"
    
    for i, result in enumerate(results, 1):
        memory_text += f"**Memory {i}** (Relevance: {result['score']:.2f})\n"
        memory_text += f"Sphere: {result['sphere']} - {result['sphere_name']}\n"
        memory_text += f"Category: {result['category']}\n"
        memory_text += f"Content: {result['content']}\n"
        if result['notion_url']:
            memory_text += f"Source: {result['notion_url']}\n"
        memory_text += "\n"
    
    memory_text += "=== END ARCHIVAL MEMORY ===\n"
    
    return memory_text


def store_memory(
    content: str,
    sphere: str,
    source: str = "grok_session",
    additional_metadata: Optional[dict] = None
) -> str:
    """
    Store new knowledge in persistent memory.
    
    Args:
        content: The knowledge to store
        sphere: Classification sphere (e.g., "S144")
        source: Where this knowledge came from
        additional_metadata: Any extra metadata to include
    
    Returns:
        The document ID of the stored memory
    """
    metadata = {
        "sphere": sphere,
        "source": source
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    doc_id = upsert_document(content, metadata)
    
    return doc_id


def enrich_prompt_with_memory(user_query: str, original_prompt: str) -> str:
    """
    Automatically enrich a prompt with relevant archival memory.
    This is the "hippocampus patch" - automatic memory recall.
    
    Args:
        user_query: What the user is asking about
        original_prompt: The original system/user prompt
    
    Returns:
        Enhanced prompt with memory context
    """
    # Recall relevant memories
    memories = recall_memory(user_query, top_k=5)
    
    # Inject before the main prompt
    enhanced = f"""{memories}

{original_prompt}

[Note: The above archival memory was automatically retrieved from Sheldonbrain OS based on semantic similarity to the current query. Use this context to provide more informed responses.]
"""
    
    return enhanced
