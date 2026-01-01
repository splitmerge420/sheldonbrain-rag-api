"""
Pinecone vector database operations.
"""

from pinecone import Pinecone, ServerlessSpec
from config import (
    PINECONE_API_KEY, 
    PINECONE_INDEX, 
    PINECONE_ENVIRONMENT,
    EMBEDDING_DIMENSIONS,
    DEFAULT_TOP_K
)
from embeddings import generate_embedding
import hashlib
from datetime import datetime

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)


def ensure_index_exists():
    """
    Create the Pinecone index if it doesn't exist.
    """
    existing_indexes = [index.name for index in pc.list_indexes()]
    
    if PINECONE_INDEX not in existing_indexes:
        print(f"📁 Creating Pinecone index: {PINECONE_INDEX}")
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIMENSIONS,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=PINECONE_ENVIRONMENT
            )
        )
        print(f"✅ Index created: {PINECONE_INDEX}")
    else:
        print(f"✅ Pinecone index exists: {PINECONE_INDEX}")


def get_index():
    """
    Get handle to the Pinecone index.
    """
    return pc.Index(PINECONE_INDEX)


def upsert_document(
    content: str,
    metadata: dict,
    namespace: str = "baseline",
    doc_id: str = None
) -> str:
    """
    Upsert a document to Pinecone.
    
    Args:
        content: The text content to embed and store
        metadata: Metadata to attach to the vector
        namespace: Pinecone namespace (for logical separation)
        doc_id: Optional document ID (will be generated if not provided)
    
    Returns:
        The document ID
    """
    index = get_index()
    
    # Generate embedding
    embedding = generate_embedding(content)
    
    # Generate doc_id if not provided
    if not doc_id:
        doc_id = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    # Add timestamp to metadata
    metadata["timestamp"] = datetime.utcnow().isoformat()
    metadata["content_preview"] = content[:200]  # Store preview for debugging
    
    # Upsert to Pinecone
    index.upsert(
        vectors=[(doc_id, embedding, metadata)],
        namespace=namespace
    )
    
    print(f"✅ Upserted document: {doc_id}")
    return doc_id


def query_similar(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    namespace: str = "baseline",
    sphere_filter: str = None
) -> list[dict]:
    """
    Query for similar documents.
    
    Args:
        query: The search query
        top_k: Number of results to return
        namespace: Pinecone namespace to search
        sphere_filter: Optional sphere to filter by (e.g., "S069")
    
    Returns:
        List of matching documents with scores and metadata
    """
    index = get_index()
    
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Build filter if sphere specified
    filter_dict = {}
    if sphere_filter:
        filter_dict["sphere"] = sphere_filter
    
    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True,
        filter=filter_dict if filter_dict else None
    )
    
    # Format results
    formatted_results = []
    for match in results.matches:
        formatted_results.append({
            "id": match.id,
            "score": match.score,
            "content": match.metadata.get("content_preview", ""),
            "sphere": match.metadata.get("sphere", ""),
            "sphere_name": match.metadata.get("sphere_name", ""),
            "category": match.metadata.get("category", ""),
            "notion_url": match.metadata.get("notion_url", ""),
            "metadata": match.metadata
        })
    
    return formatted_results


def get_index_stats(namespace: str = None) -> dict:
    """
    Get statistics about the Pinecone index.
    
    Args:
        namespace: Optional namespace to get stats for
    
    Returns:
        Dictionary with index statistics
    """
    index = get_index()
    stats = index.describe_index_stats()
    
    if namespace:
        return {
            "namespace": namespace,
            "vector_count": stats.namespaces.get(namespace, {}).get("vector_count", 0),
            "total_vectors": stats.total_vector_count
        }
    
    return {
        "total_vectors": stats.total_vector_count,
        "dimension": stats.dimension,
        "namespaces": {ns: info.vector_count for ns, info in stats.namespaces.items()}
    }
