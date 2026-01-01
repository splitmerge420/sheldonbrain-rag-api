#!/usr/bin/env python3
"""
Deep-Recall Protocol: Systematic RAG API Query
Extract all strategic insights for 2026 Master Strategy Document
"""
import requests
import json
import time
from datetime import datetime

# RAG API endpoint
RAG_URL = "https://8081-ifnw9mfmlfetwe16tj4bt-d731c093.sg1.manus.computer"

# Strategic query categories
QUERIES = [
    # Core Principles
    {
        "category": "Core Principles",
        "queries": [
            "Zero Erasure Principle",
            "Governance Unified Theory GUT",
            "To erase is to fail to conserve is to govern",
            "Adiabatic Sovereignty",
            "Joy Protocol mechanics",
            "Constitutional AI principles"
        ]
    },
    # Architecture
    {
        "category": "System Architecture",
        "queries": [
            "Multi-AI coordination infrastructure",
            "Persistent memory architecture",
            "RAG API deployment strategy",
            "Pinecone vector database",
            "Gemini embeddings integration"
        ]
    },
    # Strategic Jobs
    {
        "category": "Net Positive Jobs",
        "queries": [
            "Net Positive job definitions",
            "Restoration Army tactical primitives",
            "Sphere synthesis insights",
            "Cross-domain analysis",
            "Implementation strategies"
        ]
    },
    # Evolution & Optimization
    {
        "category": "Evolution & Optimization",
        "queries": [
            "Zapier evolution arc",
            "Progressive simplification",
            "Automation workflows",
            "Tool optimization",
            "Integration patterns"
        ]
    },
    # Governance & Systems
    {
        "category": "Governance & Systems",
        "queries": [
            "Zero-entropy governance",
            "Adiabatic sovereignty implementation",
            "Constitutional frameworks",
            "Dignity not conditional",
            "Provenance primary right"
        ]
    },
    # Meta-cognition
    {
        "category": "Meta-cognition",
        "queries": [
            "PhD insights synthesis",
            "Novelty scoring methodology",
            "Cross-AI collaboration patterns",
            "Collective intelligence emergence",
            "Meta-synthesis frameworks"
        ]
    },
    # Deployment & Operations
    {
        "category": "Deployment & Operations",
        "queries": [
            "Cloud Run deployment guide",
            "Chromebook terminal integration",
            "Production readiness checklist",
            "Cost optimization strategies",
            "Performance metrics"
        ]
    },
    # 2026 Strategy
    {
        "category": "2026 Strategic Vision",
        "queries": [
            "Restoration Army mission",
            "2026 deployment roadmap",
            "Success metrics definition",
            "Tactical playbook",
            "Strategic objectives"
        ]
    }
]

def query_rag(query_text, top_k=5):
    """Query the RAG API"""
    try:
        response = requests.post(
            f"{RAG_URL}/query",
            json={"query": query_text, "top_k": top_k},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ❌ Error querying '{query_text}': {str(e)}")
        return None

def format_result(result):
    """Format a single result for display"""
    score = result.get('score', 0)
    text = result.get('text', '')
    metadata = result.get('metadata', {})
    
    # Extract key metadata
    source = metadata.get('source', 'Unknown')
    sphere = metadata.get('sphere', metadata.get('sphere_name', 'N/A'))
    novelty = metadata.get('novelty', 'N/A')
    category = metadata.get('category', 'N/A')
    
    return {
        'score': score,
        'text': text,
        'source': source,
        'sphere': sphere,
        'novelty': novelty,
        'category': category,
        'metadata': metadata
    }

def main():
    print("=" * 80)
    print("🔥 DEEP-RECALL PROTOCOL: SYSTEMATIC RAG QUERY")
    print("=" * 80)
    print(f"Target: {RAG_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Categories: {len(QUERIES)}")
    print(f"Total Queries: {sum(len(cat['queries']) for cat in QUERIES)}")
    print("=" * 80)
    print()
    
    all_results = {}
    total_memories = 0
    
    for category_data in QUERIES:
        category = category_data['category']
        queries = category_data['queries']
        
        print(f"\n{'=' * 80}")
        print(f"📂 CATEGORY: {category}")
        print(f"{'=' * 80}")
        
        category_results = []
        
        for query in queries:
            print(f"\n🔍 Query: {query}")
            
            result = query_rag(query, top_k=5)
            
            if result and 'memories' in result:
                memories = result['memories']
                count = len(memories)
                query_time = result.get('query_time_ms', 0)
                
                print(f"  ✅ Retrieved {count} memories in {query_time:.0f}ms")
                
                formatted_memories = [format_result(m) for m in memories]
                
                category_results.append({
                    'query': query,
                    'count': count,
                    'query_time_ms': query_time,
                    'memories': formatted_memories
                })
                
                total_memories += count
                
                # Display top result
                if formatted_memories:
                    top = formatted_memories[0]
                    print(f"  📊 Top Result:")
                    print(f"     Score: {top['score']:.3f}")
                    print(f"     Source: {top['source']}")
                    print(f"     Sphere: {top['sphere']}")
                    print(f"     Novelty: {top['novelty']}")
                    if top['text']:
                        preview = top['text'][:150] + "..." if len(top['text']) > 150 else top['text']
                        print(f"     Text: {preview}")
            else:
                print(f"  ⚠️ No results")
            
            # Rate limiting
            time.sleep(0.5)
        
        all_results[category] = category_results
    
    # Save results
    output_file = f"/home/ubuntu/rag-api/deep_recall_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_categories': len(QUERIES),
            'total_queries': sum(len(cat['queries']) for cat in QUERIES),
            'total_memories_retrieved': total_memories,
            'results': all_results
        }, f, indent=2)
    
    print("\n" + "=" * 80)
    print("📊 DEEP-RECALL SUMMARY")
    print("=" * 80)
    print(f"Total Categories: {len(QUERIES)}")
    print(f"Total Queries: {sum(len(cat['queries']) for cat in QUERIES)}")
    print(f"Total Memories Retrieved: {total_memories}")
    print(f"Output File: {output_file}")
    print("=" * 80)
    
    return output_file

if __name__ == "__main__":
    output_file = main()
    print(f"\n✅ Deep-Recall complete. Results saved to: {output_file}")
