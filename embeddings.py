"""
Embedding generation using Google Gemini's text-embedding-004.
"""

from google import genai
from google.genai import types
from config import GEMINI_API_KEY, EMBEDDING_MODEL

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for a text string using Gemini.
    
    Args:
        text: String to embed (will be truncated if too long)
    
    Returns:
        List of floats (768 dimensions for text-embedding-004)
    """
    # Truncate to avoid token limits (Gemini can handle quite a bit)
    text = text[:10000]  # Conservative limit
    
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text
    )
    
    return response.embeddings[0].values


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts.
    Gemini supports batch embedding.
    
    Args:
        texts: List of strings to embed
    
    Returns:
        List of embedding vectors
    """
    # Truncate all texts
    texts = [t[:10000] for t in texts]
    
    # Gemini can handle multiple texts in one call
    embeddings = []
    for text in texts:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )
        embeddings.append(response.embeddings[0].values)
    
    return embeddings
