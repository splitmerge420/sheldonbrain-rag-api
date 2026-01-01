import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # For embeddings
XAI_API_KEY = os.getenv("XAI_API_KEY")  # Grok API
NOTION_API_KEY = os.getenv("NOTION_API_KEY")

# Pinecone Configuration
PINECONE_INDEX = "sheldonbrain-rag"
PINECONE_ENVIRONMENT = "us-east-1"  # Adjust to your region
EMBEDDING_MODEL = "text-embedding-004"  # Gemini, 768 dimensions
EMBEDDING_DIMENSIONS = 768

# Sheldonbrain OS - Database ID from your Notion
SHELDONBRAIN_DATABASE_ID = "2d20c1de73d980cea9af000b011d52f0"

# RAG Configuration
DEFAULT_TOP_K = 5
CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
