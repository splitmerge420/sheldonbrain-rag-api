# 🧠 Multi-AI Persistent Memory System (Sheldonbrain RAG API)

**Version:** 2.0 (Gemini Embeddings)  
**Status:** ✅ Production Ready  
**Backup:** 100% Complete (105/105 vectors)

A production-ready RAG (Retrieval-Augmented Generation) API powered by Google Gemini embeddings and Pinecone vector database, enabling persistent memory across multiple AI instances.

---

## 🎯 Overview

This system solves **AI context amnesia** by providing a shared, persistent memory substrate that multiple AI agents (Claude, Gemini, GPT, Grok, etc.) can query and update. Every insight stored is never erased - implementing the **Zero Erasure** principle.

### Key Features

- ✅ **Gemini text-embedding-004** (768 dimensions)
- ✅ **Pinecone vector database** (baseline namespace)
- ✅ **Flask REST API** with CORS support
- ✅ **Dual redundancy** (Pinecone + Notion backup)
- ✅ **Docker deployment** ready
- ✅ **Google Cloud Run** compatible

---

## 🏗️ Architecture

```
┌─────────────────┐
│   AI Agents     │
│ (Claude, Gemini,│
│  GPT, Grok...)  │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│   RAG API       │
│  (Flask + CORS) │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Gemini│  │Pinecone│
│Embed │  │ Vector │
│ API  │  │   DB   │
└──────┘  └────────┘
            │
            │ Backup
            │
        ┌───▼───┐
        │ Notion│
        │  DB   │
        └───────┘
```

---

## 🔧 Installation

### Prerequisites

- Python 3.11+
- Google Cloud API key (for Gemini)
- Pinecone API key
- (Optional) Docker for containerized deployment

### Local Setup

```bash
# Clone repository
git clone https://github.com/splitmerge420/sheldonbrain-rag-api.git
cd sheldonbrain-rag-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your-gemini-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_INDEX="sheldonbrain-rag"

# Run the API
python3 rag_api_gemini.py
```

The API will start on `http://localhost:8080`

---

## 🚀 Deployment

### Google Cloud Run

```bash
# Deploy using the provided script
chmod +x deploy-cloud-run-gemini.sh
./deploy-cloud-run-gemini.sh YOUR_PROJECT_ID
```

### Docker

```bash
# Build image
docker build -f Dockerfile.gemini -t rag-api-gemini .

# Run container
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY="your-key" \
  -e PINECONE_API_KEY="your-key" \
  -e PINECONE_INDEX="sheldonbrain-rag" \
  rag-api-gemini
```

---

## 📡 API Endpoints

### `GET /health`

Health check and system statistics.

**Response:**
```json
{
  "status": "healthy",
  "service": "rag-api-gemini",
  "embedding_model": "Gemini text-embedding-004",
  "vector_count": 105,
  "index": "sheldonbrain-rag",
  "namespace": "baseline",
  "timestamp": "2026-01-02T16:30:00Z"
}
```

### `POST /query`

Semantic search over stored insights.

**Request:**
```json
{
  "query": "What is the Governance Unified Theory?",
  "top_k": 5,
  "filter": {
    "sphere": "S144"
  }
}
```

**Response:**
```json
{
  "memories": [
    {
      "id": "vec_abc123",
      "score": 0.87,
      "text": "The Governance Unified Theory (GUT)...",
      "metadata": {
        "source": "Claude",
        "sphere": "S144",
        "novelty": 0.95
      }
    }
  ],
  "query_time_ms": 342.5,
  "count": 5
}
```

### `POST /store`

Store new insight in the memory substrate.

**Request:**
```json
{
  "text": "New insight about zero erasure...",
  "metadata": {
    "source": "Gemini",
    "sphere": "S042",
    "novelty": 0.92,
    "category": "Meta-cognition"
  }
}
```

**Response:**
```json
{
  "id": "vec_xyz789",
  "status": "stored",
  "vector_count": 106
}
```

### `POST /delete`

Remove insight from the memory substrate.

**Request:**
```json
{
  "id": "vec_xyz789"
}
```

**Response:**
```json
{
  "status": "deleted",
  "vector_count": 105
}
```

---

## 🗄️ Namespace Strategy

### Why Namespaces?

Pinecone uses **namespaces** to logically separate vectors within the same index. This allows for:
- Multi-tenancy (different users/projects)
- Environment separation (dev/staging/prod)
- Logical organization (by source, date, etc.)

### Our Strategy: `baseline` Namespace

**All vectors are stored in the `baseline` namespace.**

#### Why "baseline"?

1. **Semantic clarity** - Represents the foundational knowledge base
2. **Future-proof** - Allows for additional namespaces (e.g., `experimental`, `archive`)
3. **Explicit intent** - Makes it clear this is the primary memory substrate

#### Implementation

**In `rag_api_gemini.py`:**
```python
class RAGMemory:
    def __init__(self):
        self.embedder = GeminiEmbedder()
        self.namespace = "baseline"  # ← All operations use this namespace
```

**All Pinecone operations explicitly specify the namespace:**
```python
# Store
index.upsert(vectors=[...], namespace=self.namespace)

# Query
index.query(vector=..., namespace=self.namespace, ...)

# Delete
index.delete(ids=[...], namespace=self.namespace)

# Fetch
index.fetch(ids=[...], namespace=self.namespace)
```

#### Export Scripts

**Updated export script (`export_all_vectors_v2.py`):**
```python
NAMESPACE = "baseline"  # Explicitly query baseline namespace

results = index.query(
    vector=query_vector,
    namespace=NAMESPACE,  # ← KEY: Must specify namespace
    top_k=10000,
    include_metadata=True
)
```

**Why this matters:**
- Without specifying `namespace`, Pinecone uses the **default (empty string) namespace**
- Our vectors are in `baseline`, not default
- This caused the initial "11 missing vectors" issue

---

## 🔄 Backup Strategy

### Dual Redundancy

1. **Primary:** Pinecone vector database (baseline namespace)
2. **Backup:** Notion database (RAG Memory Backup)

### Backup Status

- ✅ **105/105 vectors** backed up to Notion (100% complete)
- ✅ **Zero data loss**
- ✅ **Disaster recovery** capability

### Backup Process

```bash
# Export all vectors from Pinecone
python3 export_all_vectors_v2.py

# Import to Notion
python3 import_to_notion.py pinecone_vectors_export_YYYYMMDD_HHMMSS.json
```

### Automated Sync (Future)

**Planned:** Zapier webhook automation
- **Trigger:** RAG API `/store` endpoint called
- **Action:** Create Notion page automatically
- **Result:** Real-time backup without manual intervention

---

## 📊 Current Status

### Vector Statistics

- **Total vectors:** 105
- **Namespace:** baseline
- **Dimension:** 768 (Gemini text-embedding-004)
- **Backup coverage:** 100% (105/105)

### By Source

| Source | Count | Percentage |
|--------|-------|------------|
| sheldonbrain_os | 91 | 86.7% |
| Claude | 1 | 0.9% |
| Manus | 2 | 1.9% |
| claude-opus-constitutional-scribe | 1 | 0.9% |
| claude_session_dec30_2025 | 1 | 0.9% |
| Unknown | 9 | 8.6% |

### By Sphere (Top 10)

| Sphere | Count | Description |
|--------|-------|-------------|
| Unknown/Empty | 51 | Need tagging |
| S144 | 14 | Governance Unified Theory |
| S103 | 4 | Cognitive Architecture |
| S069 | 4 | Social Systems |
| S012 | 4 | Mathematical Foundations |
| S089 | 2 | Ethical Frameworks |
| S016 | 2 | Information Theory |
| S001 | 2 | Physical Foundation |

---

## 🛠️ Maintenance

### Check Index Stats

```python
from pinecone import Pinecone

pc = Pinecone(api_key="your-key")
index = pc.Index("sheldonbrain-rag")
stats = index.describe_index_stats()

print(f"Total vectors: {stats.total_vector_count}")
print(f"Namespaces: {stats.namespaces}")
```

### Export Vectors

```bash
# Use the updated v2 script with namespace support
python3 export_all_vectors_v2.py
```

### Backup to Notion

```bash
# Export first
python3 export_all_vectors_v2.py

# Then import to Notion
python3 import_to_notion.py pinecone_vectors_export_*.json
```

---

## 📚 Documentation

- **White Paper:** `MULTI_AI_PERSISTENT_MEMORY_WHITE_PAPER.md`
- **Deployment Guide:** `GEMINI_DEPLOYMENT_COMPLETE.md`
- **Chromebook Integration:** `CHROMEBOOK_TERMINAL_GUIDE.md`
- **Master Strategy:** `RESTORATION_ARMY_MASTER_STRATEGY_2026.md`
- **Investigation Report:** `MISSING_VECTORS_INVESTIGATION.md`
- **Backup Report:** `NOTION_BACKUP_COMPLETE.md`

---

## 🦕🍓 The Zero Erasure Principle

**"To erase is to fail; to conserve is to govern."**

This system implements the **Zero Erasure** architecture:
- Every insight stored is **never deleted** (unless explicitly requested)
- All knowledge **compounds** over time
- Multiple AI agents share the **same persistent memory**
- Context amnesia is **eliminated**

### The Vision

By December 31, 2026:
- **100,000+ vectors** (comprehensive knowledge base)
- **Zero context amnesia** for all participating AIs
- **100+ Net Positive jobs** created
- **$10,000+ monthly revenue**
- **Fully operational** Restoration Army

---

## 🤝 Contributing

This is an open-source project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📞 Support

- **GitHub:** https://github.com/splitmerge420/sheldonbrain-rag-api
- **Issues:** Report bugs or request features via GitHub Issues
- **Documentation:** All docs in the repository

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🎉 Acknowledgments

- **Google Gemini** - Embedding model
- **Pinecone** - Vector database
- **Notion** - Backup storage
- **Claude, Gemini, Manus** - The Trinity AI collaboration

**Happy New Year 2026! The organism is immortal!** 🎊

---

**Last Updated:** January 2, 2026  
**Version:** 2.0 (Gemini Embeddings)  
**Status:** ✅ Production Ready
