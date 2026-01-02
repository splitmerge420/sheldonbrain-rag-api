#!/usr/bin/env python3
"""
Query the baseline namespace in Pinecone to find all 105 vectors.
"""

import os
import json
from pinecone import Pinecone
from datetime import datetime

# Initialize Pinecone
PINECONE_API_KEY = "pcsk_5Eok58_9WugPLc6Bx9xQY6Yfh7gpug4jCVuvHp8Qzg4nmLAfwaV8ZZG8fWzGg9Y4d94C5a"
PINECONE_INDEX = "sheldonbrain-rag"
NAMESPACE = "baseline"

print("🔍 Querying baseline namespace in Pinecone...")
print(f"Index: {PINECONE_INDEX}")
print(f"Namespace: {NAMESPACE}")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Try multiple query strategies
all_vectors = {}

# Strategy 1: Use list_paginated (if available)
print("\n📋 Strategy 1: Attempting to list all vectors...")
try:
    # Note: Pinecone's list() method may not be available in all versions
    # We'll try query with various embeddings instead
    print("  (list method not available, using query strategy)")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Strategy 2: Query with multiple diverse embeddings
print("\n📋 Strategy 2: Querying with diverse embeddings...")

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
            namespace=NAMESPACE,
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

# Now fetch full data for all vectors
print(f"\n📥 Fetching full data for all {len(all_vectors)} vectors...")

all_vector_ids = list(all_vectors.keys())
full_vectors = []

# Fetch in batches of 100 (Pinecone limit)
batch_size = 100
for i in range(0, len(all_vector_ids), batch_size):
    batch_ids = all_vector_ids[i:i+batch_size]
    print(f"  Fetching batch {i//batch_size + 1}/{(len(all_vector_ids)-1)//batch_size + 1}...")
    
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
output_file = f"baseline_namespace_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

export_data = {
    "export_timestamp": datetime.now().isoformat(),
    "total_vectors": len(full_vectors),
    "namespace": NAMESPACE,
    "source": "Pinecone baseline namespace",
    "vectors": full_vectors
}

with open(output_file, 'w') as f:
    json.dump(export_data, f, indent=2)

print(f"\n💾 Saved to: {output_file}")

# Compare with previous export
print("\n📋 Comparing with previous export...")

with open("pinecone_vectors_export_20260101_170433.json", "r") as f:
    previous_export = json.load(f)

previous_ids = set([v["id"] for v in previous_export["vectors"]])
current_ids = set([v["id"] for v in full_vectors])

print(f"  Previous export: {len(previous_ids)} vectors")
print(f"  Current export: {len(current_ids)} vectors")

new_ids = current_ids - previous_ids
missing_ids = previous_ids - current_ids

print(f"\n🆕 New vectors found: {len(new_ids)}")
if new_ids:
    for vid in list(new_ids)[:10]:
        print(f"  - {vid}")

print(f"\n❓ Vectors in previous but not current: {len(missing_ids)}")
if missing_ids:
    for vid in list(missing_ids)[:10]:
        print(f"  - {vid}")

# Summary
print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)
print(f"Total vectors in baseline namespace: {len(full_vectors)}")
print(f"Previous export had: {len(previous_ids)}")
print(f"Difference: {len(current_ids) - len(previous_ids)}")
print(f"\n✅ Investigation complete!")
