#!/usr/bin/env python3
"""
Batch import vectors from Pinecone export to Notion RAG Memory Backup database.
"""

import json
import subprocess
import time
from datetime import datetime

def import_to_notion(export_file):
    """
    Import all vectors from export file to Notion using MCP CLI.
    """
    
    print(f"📥 Importing vectors from: {export_file}")
    
    # Load export data
    with open(export_file, 'r') as f:
        data = json.load(f)
    
    vectors = data.get("vectors", [])
    total = len(vectors)
    
    print(f"📊 Total vectors to import: {total}")
    
    # Notion database ID (from Claude's message)
    database_id = "0dfb9192c47047f3b0c2002368ec2139"
    
    success_count = 0
    error_count = 0
    errors = []
    
    for idx, vector in enumerate(vectors, 1):
        vector_id = vector.get("id", f"vec_{idx}")
        text = vector.get("text", "")
        score = vector.get("score", 0.0)
        metadata = vector.get("metadata", {})
        
        # Extract metadata fields
        source = metadata.get("source", "Unknown")
        sphere = metadata.get("sphere", "")
        novelty = metadata.get("novelty", 0.0)
        category = metadata.get("category", "")
        timestamp = metadata.get("timestamp", datetime.now().isoformat())
        
        # Truncate text if too long (Notion has limits)
        content_preview = text[:2000] if len(text) > 2000 else text
        
        print(f"\n[{idx}/{total}] Importing: {vector_id[:20]}...")
        print(f"  Source: {source} | Sphere: {sphere or 'N/A'} | Novelty: {novelty}")
        
        # Prepare Notion page in Markdown format
        page_title = f"{vector_id[:30]}..."
        page_content = f"""# {vector_id}

## Content

{content_preview}

## Metadata

- **Source:** {source}
- **Sphere:** {sphere or 'N/A'}
- **Novelty Score:** {novelty}
- **Similarity Score:** {score}
- **Category:** {category or 'N/A'}
- **Timestamp:** {timestamp}
"""
        
        # Prepare notion-create-pages input
        notion_input = {
            "parent": {
                "data_source_id": database_id
            },
            "pages": [
                {
                    "title": page_title,
                    "content": page_content
                }
            ]
        }
        
        # Call Notion MCP to create pages
        try:
            result = subprocess.run(
                [
                    "manus-mcp-cli", "tool", "call", "notion-create-pages",
                    "--server", "notion",
                    "--input", json.dumps(notion_input)
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"  ✅ Success")
                success_count += 1
            else:
                print(f"  ❌ Error: {result.stderr[:100]}")
                error_count += 1
                errors.append({
                    "vector_id": vector_id,
                    "error": result.stderr[:200]
                })
        
        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:100]}")
            error_count += 1
            errors.append({
                "vector_id": vector_id,
                "error": str(e)[:200]
            })
        
        # Rate limiting - don't overwhelm Notion API
        if idx % 10 == 0:
            print(f"\n⏸️  Pausing for rate limiting... ({idx}/{total} complete)")
            time.sleep(2)
    
    # Final report
    print(f"\n" + "="*60)
    print(f"📊 IMPORT COMPLETE")
    print(f"="*60)
    print(f"✅ Success: {success_count}/{total}")
    print(f"❌ Errors: {error_count}/{total}")
    
    if errors:
        print(f"\n⚠️  Error Details:")
        for err in errors[:5]:  # Show first 5 errors
            print(f"  - {err['vector_id']}: {err['error'][:100]}")
    
    # Save error log
    if errors:
        error_file = f"notion_import_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)
        print(f"\n📝 Full error log saved to: {error_file}")
    
    return success_count, error_count

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 import_to_notion.py <export_file.json>")
        sys.exit(1)
    
    export_file = sys.argv[1]
    success, errors = import_to_notion(export_file)
    
    print(f"\n🎉 Import process complete!")
    print(f"✅ {success} vectors successfully imported to Notion")
    if errors > 0:
        print(f"⚠️  {errors} vectors failed (see error log)")
