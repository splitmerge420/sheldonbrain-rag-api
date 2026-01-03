#!/usr/bin/env python3
"""
Batch Ingestion Pipeline for RAG System

Ingests multiple files in parallel with:
- Metadata validation
- Rate limiting
- Error recovery
- Automatic Notion backup
- Progress tracking
"""

import os
import sys
import json
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from metadata_validator import MetadataValidator

# Configuration
RAG_API_URL = os.getenv("RAG_API_URL", "https://8081-ifnw9mfmlfetwe16tj4bt-d731c093.sg1.manus.computer")
NOTION_DATABASE_ID = "0dfb9192c47047f3b0c2002368ec2139"
BATCH_SIZE = 10  # Parallel workers
RATE_LIMIT_DELAY = 1.0  # Seconds between requests
MAX_RETRIES = 3
RETRY_DELAY = 2  # Seconds

class BatchIngestionPipeline:
    """Parallel batch ingestion pipeline with validation and backup"""
    
    def __init__(self, rag_api_url: str = RAG_API_URL, batch_size: int = BATCH_SIZE):
        self.rag_api_url = rag_api_url
        self.batch_size = batch_size
        self.validator = MetadataValidator()
        self.stats = {
            "total_files": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None
        }
        self.results = []
        self.failed_files = []
    
    def read_file_content(self, file_path: str) -> str:
        """Read and clean file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove YAML frontmatter if present
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            
            return content
        
        except Exception as e:
            raise ValueError(f"Could not read file: {e}")
    
    def ingest_single_file(self, file_path: str, auto_backup: bool = True) -> Dict:
        """
        Ingest a single file with metadata validation.
        
        Returns:
            {
                "file_path": str,
                "status": "success" | "failed" | "skipped",
                "vector_id": str (if successful),
                "error": str (if failed),
                "metadata": dict,
                "backed_up": bool
            }
        """
        result = {
            "file_path": file_path,
            "status": "failed",
            "vector_id": None,
            "error": None,
            "metadata": {},
            "backed_up": False
        }
        
        try:
            # Step 1: Validate metadata
            print(f"  📋 Validating metadata: {Path(file_path).name}")
            metadata = self.validator.validate_metadata(file_path, auto_enrich=True)
            result["metadata"] = metadata
            
            # Step 2: Read content
            print(f"  📖 Reading content: {Path(file_path).name}")
            content = self.read_file_content(file_path)
            
            if not content or len(content.strip()) < 10:
                result["status"] = "skipped"
                result["error"] = "Content too short or empty"
                return result
            
            # Step 3: Store in RAG API
            print(f"  🚀 Storing in RAG: {Path(file_path).name}")
            
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = requests.post(
                        f"{self.rag_api_url}/store",
                        json={
                            "text": content,
                            "metadata": metadata
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        result["vector_id"] = data.get("id")
                        result["status"] = "success"
                        print(f"  ✅ Stored: {result['vector_id']}")
                        break
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                        if attempt < MAX_RETRIES:
                            print(f"  ⚠️  Attempt {attempt} failed, retrying...")
                            time.sleep(RETRY_DELAY * attempt)
                        else:
                            result["error"] = error_msg
                            return result
                
                except Exception as e:
                    error_msg = str(e)
                    if attempt < MAX_RETRIES:
                        print(f"  ⚠️  Attempt {attempt} failed: {error_msg}, retrying...")
                        time.sleep(RETRY_DELAY * attempt)
                    else:
                        result["error"] = error_msg
                        return result
            
            # Step 4: Backup to Notion (if enabled and successful)
            if auto_backup and result["status"] == "success":
                print(f"  💾 Backing up to Notion: {Path(file_path).name}")
                try:
                    self.backup_to_notion(result["vector_id"], content, metadata)
                    result["backed_up"] = True
                    print(f"  ✅ Backed up to Notion")
                except Exception as e:
                    print(f"  ⚠️  Notion backup failed: {e}")
                    # Don't fail the whole operation if backup fails
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
            return result
        
        except Exception as e:
            result["error"] = str(e)
            return result
    
    def backup_to_notion(self, vector_id: str, content: str, metadata: Dict):
        """Backup vector to Notion database"""
        # Prepare Notion page content
        content_preview = content[:2000] if content else "(empty)"
        page_title = f"{vector_id}"
        
        source = metadata.get("source", "Unknown")
        sphere = metadata.get("sphere", "N/A")
        novelty = metadata.get("novelty", 0.0)
        category = metadata.get("category", "")
        timestamp = metadata.get("timestamp", "")
        
        page_content = f"""# {vector_id}

## Content

{content_preview}

## Metadata

- **Source:** {source}
- **Sphere:** {sphere}
- **Novelty Score:** {novelty}
- **Category:** {category}
- **Timestamp:** {timestamp}
"""
        
        # Call Notion MCP
        notion_input = {
            "parent": {
                "data_source_id": NOTION_DATABASE_ID
            },
            "pages": [
                {
                    "title": page_title,
                    "content": page_content
                }
            ]
        }
        
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
        
        if result.returncode != 0:
            raise Exception(f"Notion API error: {result.stderr[:200]}")
    
    def ingest_batch(self, file_paths: List[str], auto_backup: bool = True) -> Dict:
        """
        Ingest a batch of files in parallel.
        
        Returns:
            {
                "results": [result_dict, ...],
                "stats": {...}
            }
        """
        print(f"\n🚀 Ingesting batch of {len(file_paths)} files...")
        print(f"   Parallel workers: {self.batch_size}")
        print(f"   Auto-backup: {auto_backup}")
        
        batch_results = []
        
        with ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self.ingest_single_file, fp, auto_backup): fp
                for fp in file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    batch_results.append(result)
                    
                    # Update stats
                    if result["status"] == "success":
                        self.stats["successful"] += 1
                    elif result["status"] == "failed":
                        self.stats["failed"] += 1
                        self.failed_files.append((file_path, result["error"]))
                    else:
                        self.stats["skipped"] += 1
                    
                    # Progress
                    completed = len(batch_results)
                    total = len(file_paths)
                    pct = (completed / total) * 100
                    print(f"\n📊 Progress: {completed}/{total} ({pct:.1f}%)")
                    print(f"   ✅ Success: {self.stats['successful']}")
                    print(f"   ❌ Failed: {self.stats['failed']}")
                    print(f"   ⏭️  Skipped: {self.stats['skipped']}")
                
                except Exception as e:
                    print(f"❌ Unexpected error for {file_path}: {e}")
                    batch_results.append({
                        "file_path": file_path,
                        "status": "failed",
                        "error": str(e)
                    })
                    self.stats["failed"] += 1
                    self.failed_files.append((file_path, str(e)))
        
        return {
            "results": batch_results,
            "stats": self.stats
        }
    
    def ingest_all(self, file_paths: List[str], auto_backup: bool = True) -> Dict:
        """
        Ingest all files with progress tracking.
        
        Splits into batches for better progress reporting.
        """
        self.stats["total_files"] = len(file_paths)
        self.stats["start_time"] = datetime.now().isoformat()
        
        print(f"\n🔥 STARTING BATCH INGESTION")
        print(f"   Total files: {len(file_paths)}")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Auto-backup: {auto_backup}")
        print(f"   RAG API: {self.rag_api_url}")
        
        # Process all files
        result = self.ingest_batch(file_paths, auto_backup)
        self.results = result["results"]
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        # Calculate duration
        start = datetime.fromisoformat(self.stats["start_time"])
        end = datetime.fromisoformat(self.stats["end_time"])
        duration = (end - start).total_seconds()
        self.stats["duration_seconds"] = duration
        self.stats["files_per_minute"] = (self.stats["successful"] / duration) * 60 if duration > 0 else 0
        
        # Print final report
        self.print_report()
        
        return {
            "results": self.results,
            "stats": self.stats,
            "failed_files": self.failed_files
        }
    
    def print_report(self):
        """Print final ingestion report"""
        print(f"\n\n{'='*60}")
        print(f"🎉 BATCH INGESTION COMPLETE")
        print(f"{'='*60}")
        
        print(f"\n📊 Statistics:")
        print(f"   Total files: {self.stats['total_files']}")
        print(f"   ✅ Successful: {self.stats['successful']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print(f"   ⏭️  Skipped: {self.stats['skipped']}")
        
        success_rate = (self.stats['successful'] / self.stats['total_files']) * 100 if self.stats['total_files'] > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        
        print(f"\n⏱️  Performance:")
        print(f"   Duration: {self.stats['duration_seconds']:.1f} seconds")
        print(f"   Speed: {self.stats['files_per_minute']:.1f} files/minute")
        
        if self.failed_files:
            print(f"\n❌ Failed files:")
            for file_path, error in self.failed_files[:10]:
                print(f"   {Path(file_path).name}: {error[:100]}")
            
            if len(self.failed_files) > 10:
                print(f"   ... and {len(self.failed_files) - 10} more")
        
        print(f"\n{'='*60}\n")
    
    def save_report(self, output_file: str):
        """Save detailed report to JSON"""
        report = {
            "stats": self.stats,
            "results": self.results,
            "failed_files": [{"file": f, "error": e} for f, e in self.failed_files]
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {output_file}")


def main():
    """CLI interface for batch ingestion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch ingest files into RAG system")
    parser.add_argument("input", help="File or directory to ingest")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Number of parallel workers")
    parser.add_argument("--no-backup", action="store_true", help="Disable automatic Notion backup")
    parser.add_argument("--rag-api", default=RAG_API_URL, help="RAG API URL")
    parser.add_argument("--report", help="Save report to JSON file")
    
    args = parser.parse_args()
    
    # Collect files
    if os.path.isfile(args.input):
        file_paths = [args.input]
    elif os.path.isdir(args.input):
        file_paths = [
            os.path.join(args.input, f)
            for f in os.listdir(args.input)
            if f.endswith(('.md', '.txt'))
        ]
    else:
        print(f"❌ Path not found: {args.input}")
        sys.exit(1)
    
    if not file_paths:
        print(f"❌ No files found in: {args.input}")
        sys.exit(1)
    
    # Create pipeline
    pipeline = BatchIngestionPipeline(
        rag_api_url=args.rag_api,
        batch_size=args.batch_size
    )
    
    # Ingest
    result = pipeline.ingest_all(
        file_paths,
        auto_backup=not args.no_backup
    )
    
    # Save report
    if args.report:
        pipeline.save_report(args.report)
    
    # Exit code
    if result["stats"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
