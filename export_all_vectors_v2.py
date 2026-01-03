#!/usr/bin/env python3
"""
Export all vectors from Pinecone RAG API to JSON for Notion backup.

Version 2.0 - Updated to use baseline namespace directly via Pinecone SDK.
"""

import json
import os
from datetime import datetime
from pinecone import Pinecone

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_5Eok58_9WugPLc6Bx9xQY6Yfh7gpug4jCVuvHp8Qzg4nmLAfwaV8ZZG8fWzGg9Y4d94C5a")
PINECONE_INDEX = "sheldonbrain-rag"
NAMESPACE = "baseline"  # All vectors are stored in the baseline namespace

def export_all_vectors():
    """
    Export all vectors by querying the baseline namespace directly.
    Uses multiple diverse query vectors to ensure complete coverage.
    """
    
    print("🔍 Exporting all vectors from Pinecone...")
    print(f"Index: {PINECONE_INDEX}")
    print(f"Namespace: {NAMESPACE}")
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    
    # Get index stats
    stats = index.describe_index_stats()
    print(f"\n📊 Index Stats:")
    print(f"  Total vectors: {stats.total_vector_count}")
    print(f"  Dimension: {stats.dimension}")
    
    if hasattr(stats, 'namespaces'):
        print(f"\n📂 Namespaces:")
        for ns, ns_stats in stats.namespaces.items():
            ns_name = ns if ns else "(default)"
            print(f"  {ns_name}: {ns_stats.vector_count} vectors")
    
    # Query with diverse embeddings to get all vectors
    print(f"\n🔎 Querying {NAMESPACE} namespace...")
    
    all_vectors = {}
    
    # Generate diverse query vectors
    import random
    random.seed(42)
    
    query_strategies = [
        ("zeros", [0.0] * 768),
        ("ones", [1.0] * 768),
        ("random_1", [random.gauss(0, 0.1) for _ in range(768)]),
        ("random_2", [random.gauss(0, 0.2) for _ in range(768)]),
        ("random_3", [random.gauss(0, 0.3) for _ in range(768)]),
    ]
    
    for strategy_name, query_vector in query_strategies:
        print(f"\n  Trying {strategy_name}...")
        try:
            results = index.query(
                vector=query_vector,
                namespace=NAMESPACE,  # ← KEY: Specify namespace
                top_k=10000,
                include_metadata=True,
                include_values=False
            )
            
            print(f"    Retrieved {len(results.matches)} vectors")
            
            # Add to collection
            for match in results.matches:
                if match.id not in all_vectors:
                    all_vectors[match.id] = {
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata if hasattr(match, 'metadata') else {}
                    }
            
            print(f"    Total unique vectors so far: {len(all_vectors)}")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"\n📊 Total unique vectors collected: {len(all_vectors)}")
    
    # Fetch full data for all vectors
    print(f"\n📥 Fetching full data for all {len(all_vectors)} vectors...")
    
    all_vector_ids = list(all_vectors.keys())
    full_vectors = []
    
    # Fetch in batches of 100 (Pinecone limit)
    batch_size = 100
    for i in range(0, len(all_vector_ids), batch_size):
        batch_ids = all_vector_ids[i:i+batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(all_vector_ids)-1)//batch_size + 1
        print(f"  Fetching batch {batch_num}/{total_batches}...")
        
        try:
            fetch_result = index.fetch(ids=batch_ids, namespace=NAMESPACE)
            
            for vid, vector_data in fetch_result.vectors.items():
                metadata = vector_data.metadata if hasattr(vector_data, 'metadata') else {}
                
                # Extract text from metadata
                text = metadata.get('text', '')
                
                full_vectors.append({
                    "id": vid,
                    "text": text,
                    "score": all_vectors[vid]["score"],
                    "metadata": metadata
                })
            
            print(f"    ✅ Fetched {len(fetch_result.vectors)} vectors")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"\n✅ Total vectors with full data: {len(full_vectors)}")
    
    # Save to JSON
    output_file = f"pinecone_vectors_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_vectors": len(full_vectors),
        "namespace": NAMESPACE,
        "source": f"Pinecone {NAMESPACE} namespace",
        "index": PINECONE_INDEX,
        "vectors": full_vectors
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Print summary
    print("\n📋 Export Summary:")
    print(f"  Total vectors: {len(full_vectors)}")
    
    # Count by source
    sources = {}
    spheres = {}
    for v in full_vectors:
        metadata = v.get("metadata", {})
        source = metadata.get("source", "Unknown")
        sphere = metadata.get("sphere", "Unknown")
        
        sources[source] = sources.get(source, 0) + 1
        spheres[sphere] = spheres.get(sphere, 0) + 1
    
    print(f"\n  By Source:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"    {source}: {count}")
    
    print(f"\n  By Sphere (top 10):")
    for sphere, count in sorted(spheres.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {sphere}: {count}")
    
    return output_file, full_vectors

if __name__ == "__main__":
    output_file, vectors = export_all_vectors()
    print(f"\n🎉 Export complete! File: {output_file}")
    print(f"📦 Ready for Notion import: {len(vectors)} vectors")
