"""
Flask API for RAG operations.
Provides HTTP endpoints for querying and storing memories.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pinecone_client import query_similar, upsert_document, get_index_stats
from rag_wrapper import recall_memory, store_memory
from grok_rag import grok_with_rag
from notion_sync import full_sync
import os

app = Flask(__name__)
CORS(app)


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint.
    Returns index statistics.
    """
    try:
        stats = get_index_stats()
        return jsonify({
            "status": "healthy",
            "pinecone_stats": stats,
            "api_keys_configured": {
                "pinecone": bool(os.getenv("PINECONE_API_KEY")),
                "openai": bool(os.getenv("OPENAI_API_KEY")),
                "xai": bool(os.getenv("XAI_API_KEY")),
                "notion": bool(os.getenv("NOTION_API_KEY"))
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/query', methods=['POST'])
def query():
    """
    Query for similar memories.
    
    Body:
        {
            "query": "search query",
            "top_k": 5,
            "sphere_filter": "S069"  // optional
        }
    """
    try:
        data = request.json
        query_text = data.get("query")
        top_k = data.get("top_k", 5)
        sphere_filter = data.get("sphere_filter")
        
        if not query_text:
            return jsonify({"error": "query is required"}), 400
        
        results = query_similar(
            query=query_text,
            top_k=top_k,
            sphere_filter=sphere_filter
        )
        
        return jsonify({
            "success": True,
            "query": query_text,
            "results": results,
            "count": len(results)
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/recall', methods=['POST'])
def recall():
    """
    Recall memories in formatted text (for prompt injection).
    
    Body:
        {
            "query": "search query",
            "top_k": 5,
            "sphere_filter": "S069"  // optional
        }
    """
    try:
        data = request.json
        query_text = data.get("query")
        top_k = data.get("top_k", 5)
        sphere_filter = data.get("sphere_filter")
        
        if not query_text:
            return jsonify({"error": "query is required"}), 400
        
        memories = recall_memory(
            query=query_text,
            top_k=top_k,
            sphere_filter=sphere_filter
        )
        
        return jsonify({
            "success": True,
            "query": query_text,
            "memories": memories
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/store', methods=['POST'])
def store():
    """
    Store new memory.
    
    Body:
        {
            "content": "text to store",
            "sphere": "S016",
            "source": "grok_session",
            "metadata": {}  // optional additional metadata
        }
    """
    try:
        data = request.json
        content = data.get("content")
        sphere = data.get("sphere", "S016")
        source = data.get("source", "api")
        additional_metadata = data.get("metadata", {})
        
        if not content:
            return jsonify({"error": "content is required"}), 400
        
        doc_id = store_memory(
            content=content,
            sphere=sphere,
            source=source,
            additional_metadata=additional_metadata
        )
        
        return jsonify({
            "success": True,
            "document_id": doc_id
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/grok', methods=['POST'])
def grok():
    """
    Query Grok with RAG enhancement.
    
    Body:
        {
            "message": "user message",
            "model": "grok-beta",  // optional
            "auto_recall": true,  // optional
            "auto_store": false,  // optional
            "conversation_history": []  // optional
        }
    """
    try:
        data = request.json
        message = data.get("message")
        model = data.get("model", "grok-beta")
        auto_recall = data.get("auto_recall", True)
        auto_store = data.get("auto_store", False)
        conversation_history = data.get("conversation_history", [])
        
        if not message:
            return jsonify({"error": "message is required"}), 400
        
        result = grok_with_rag(
            user_message=message,
            model=model,
            auto_recall=auto_recall,
            auto_store=auto_store,
            conversation_history=conversation_history
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/sync', methods=['POST'])
def sync():
    """
    Trigger full sync from Notion to Pinecone.
    """
    try:
        synced_count = full_sync()
        return jsonify({
            "success": True,
            "synced_count": synced_count
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
