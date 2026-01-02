#!/usr/bin/env python3
"""
Investigate the 11 missing vectors by querying Pinecone directly.
"""

import os
from pinecone import Pinecone

# Initialize Pinecone
PINECONE_API_KEY = "pcsk_5Eok58_9WugPLc6Bx9xQY6Yfh7gpug4jCVuvHp8Qzg4nmLAfwaV8ZZG8fWzGg9Y4d94C5a"
PINECONE_INDEX = "sheldonbrain-rag"

print("🔍 Investigating missing vectors...")
print(f"Connecting to Pinecone index: {PINECONE_INDEX}")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Get index stats
print("\n📊 Querying index stats...")
stats = index.describe_index_stats()

print(f"\n✅ Index Stats:")
print(f"  Total vectors: {stats.total_vector_count}")
print(f"  Dimension: {stats.dimension}")

if hasattr(stats, 'namespaces'):
    print(f"\n📂 Namespaces:")
    for namespace, ns_stats in stats.namespaces.items():
        namespace_name = namespace if namespace else "(default)"
        print(f"  {namespace_name}: {ns_stats.vector_count} vectors")

# Try to list vectors using query with random vector
print("\n🔎 Attempting to retrieve all vectors using dummy query...")

# Create a dummy query vector (all zeros)
dummy_vector = [0.0] * 768

try:
    # Query with dummy vector to get all results
    results = index.query(
        vector=dummy_vector,
        top_k=10000,  # Request maximum
        include_metadata=True
    )
    
    print(f"\n✅ Retrieved {len(results.matches)} vectors using dummy query")
    
    # Print some sample IDs
    if results.matches:
        print(f"\nSample Vector IDs (first 10):")
        for i, match in enumerate(results.matches[:10]):
            print(f"  {i+1}. {match.id} (score: {match.score:.4f})")
    
    # Save all IDs to file
    all_ids = [match.id for match in results.matches]
    
    import json
    with open("pinecone_all_vector_ids.json", "w") as f:
        json.dump({
            "total_count": len(all_ids),
            "vector_ids": all_ids
        }, f, indent=2)
    
    print(f"\n💾 Saved all {len(all_ids)} vector IDs to: pinecone_all_vector_ids.json")
    
except Exception as e:
    print(f"\n❌ Error querying with dummy vector: {e}")

# Now compare with our export
print("\n📋 Comparing with export...")

import json
with open("pinecone_vectors_export_20260101_170433.json", "r") as f:
    export_data = json.load(f)

exported_ids = set([v["id"] for v in export_data["vectors"]])
print(f"  Exported vectors: {len(exported_ids)}")

if 'all_ids' in locals():
    pinecone_ids = set(all_ids)
    print(f"  Pinecone vectors: {len(pinecone_ids)}")
    
    missing_ids = pinecone_ids - exported_ids
    print(f"\n🔍 Missing vectors: {len(missing_ids)}")
    
    if missing_ids:
        print(f"\nMissing Vector IDs:")
        for vid in list(missing_ids)[:20]:  # Show first 20
            print(f"  - {vid}")
        
        # Try to fetch these vectors
        print(f"\n📥 Fetching missing vectors...")
        
        missing_vectors = []
        for vid in missing_ids:
            try:
                fetch_result = index.fetch(ids=[vid])
                if vid in fetch_result.vectors:
                    vector_data = fetch_result.vectors[vid]
                    missing_vectors.append({
                        "id": vid,
                        "metadata": vector_data.metadata if hasattr(vector_data, 'metadata') else {},
                        "values": vector_data.values[:10] if hasattr(vector_data, 'values') else []  # First 10 dims
                    })
                    print(f"  ✅ Fetched: {vid}")
            except Exception as e:
                print(f"  ❌ Error fetching {vid}: {e}")
        
        # Save missing vectors
        with open("missing_vectors.json", "w") as f:
            json.dump({
                "count": len(missing_vectors),
                "vectors": missing_vectors
            }, f, indent=2)
        
        print(f"\n💾 Saved {len(missing_vectors)} missing vectors to: missing_vectors.json")

print("\n✅ Investigation complete!")
