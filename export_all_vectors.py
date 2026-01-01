#!/usr/bin/env python3
"""
Export all vectors from Pinecone RAG API to JSON for Notion backup.
"""

import json
import requests
from datetime import datetime

# RAG API endpoint
RAG_API_URL = "https://8081-ifnw9mfmlfetwe16tj4bt-d731c093.sg1.manus.computer"

def export_all_vectors():
    """
    Export all vectors by querying with a generic query and high top_k.
    Since Pinecone doesn't have a direct 'list all' endpoint, we'll use
    a broad query to retrieve all vectors.
    """
    
    print("🔍 Exporting all vectors from Pinecone RAG API...")
    print(f"API URL: {RAG_API_URL}")
    
    # Query with generic terms to get all vectors
    # We'll use multiple broad queries to ensure we get everything
    broad_queries = [
        "governance theory knowledge",
        "zero erasure memory",
        "AI collaboration",
        "PhD insights research",
        "system architecture"
    ]
    
    all_vectors = {}
    
    for query in broad_queries:
        print(f"\n📡 Querying: '{query}'")
        
        try:
            response = requests.post(
                f"{RAG_API_URL}/query",
                json={"query": query, "top_k": 50},  # Get up to 50 per query
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])
                
                print(f"✅ Retrieved {len(memories)} vectors")
                
                # Add to collection (using ID as key to avoid duplicates)
                for memory in memories:
                    vector_id = memory.get("id")
                    if vector_id and vector_id not in all_vectors:
                        all_vectors[vector_id] = memory
                        
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    # Convert to list
    vectors_list = list(all_vectors.values())
    
    print(f"\n📊 Total unique vectors collected: {len(vectors_list)}")
    
    # Save to JSON
    output_file = f"pinecone_vectors_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_vectors": len(vectors_list),
        "source": "Pinecone RAG API",
        "api_url": RAG_API_URL,
        "vectors": vectors_list
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n✅ Exported to: {output_file}")
    
    # Print summary
    print("\n📋 Export Summary:")
    print(f"  Total vectors: {len(vectors_list)}")
    
    # Count by source
    sources = {}
    spheres = {}
    for v in vectors_list:
        metadata = v.get("metadata", {})
        source = metadata.get("source", "Unknown")
        sphere = metadata.get("sphere", "Unknown")
        
        sources[source] = sources.get(source, 0) + 1
        spheres[sphere] = spheres.get(sphere, 0) + 1
    
    print(f"\n  By Source:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"    {source}: {count}")
    
    print(f"\n  By Sphere:")
    for sphere, count in sorted(spheres.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {sphere}: {count}")
    
    return output_file, vectors_list

if __name__ == "__main__":
    output_file, vectors = export_all_vectors()
    print(f"\n🎉 Export complete! File: {output_file}")
    print(f"📦 Ready for Notion import: {len(vectors)} vectors")
