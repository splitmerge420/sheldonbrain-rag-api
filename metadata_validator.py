#!/usr/bin/env python3
"""
Metadata Validator for RAG Ingestion Pipeline

Validates and enriches metadata for files before ingestion.
Ensures all required fields are present and properly formatted.
"""

import os
import re
import yaml
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

# 144 Spheres taxonomy (subset for validation)
VALID_SPHERES = [
    "S001", "S002", "S003", "S004", "S005", "S006", "S007", "S008", "S009", "S010",
    "S011", "S012", "S013", "S014", "S015", "S016", "S017", "S018", "S019", "S020",
    "S021", "S022", "S023", "S024", "S025", "S026", "S027", "S028", "S029", "S030",
    "S031", "S032", "S033", "S034", "S035", "S036", "S037", "S038", "S039", "S040",
    "S041", "S042", "S043", "S044", "S045", "S046", "S047", "S048", "S049", "S050",
    "S051", "S052", "S053", "S054", "S055", "S056", "S057", "S058", "S059", "S060",
    "S061", "S062", "S063", "S064", "S065", "S066", "S067", "S068", "S069", "S070",
    "S071", "S072", "S073", "S074", "S075", "S076", "S077", "S078", "S079", "S080",
    "S081", "S082", "S083", "S084", "S085", "S086", "S087", "S088", "S089", "S090",
    "S091", "S092", "S093", "S094", "S095", "S096", "S097", "S098", "S099", "S100",
    "S101", "S102", "S103", "S104", "S105", "S106", "S107", "S108", "S109", "S110",
    "S111", "S112", "S113", "S114", "S115", "S116", "S117", "S118", "S119", "S120",
    "S121", "S122", "S123", "S124", "S125", "S126", "S127", "S128", "S129", "S130",
    "S131", "S132", "S133", "S134", "S135", "S136", "S137", "S138", "S139", "S140",
    "S141", "S142", "S143", "S144"
]

# Sphere keywords for auto-assignment
SPHERE_KEYWORDS = {
    "S001": ["physics", "matter", "energy", "quantum", "thermodynamics"],
    "S012": ["mathematics", "algebra", "calculus", "geometry", "topology"],
    "S015": ["engineering", "systems", "architecture", "infrastructure", "design"],
    "S016": ["information", "data", "entropy", "communication", "signal"],
    "S025": ["governance", "policy", "regulation", "administration", "control"],
    "S038": ["philosophy", "ethics", "metaphysics", "epistemology", "ontology"],
    "S042": ["meta-cognition", "thinking", "awareness", "consciousness", "reflection"],
    "S060": ["economics", "finance", "markets", "trade", "capital"],
    "S069": ["social", "community", "society", "culture", "relationships"],
    "S089": ["ethics", "morality", "values", "principles", "justice"],
    "S103": ["cognition", "intelligence", "reasoning", "learning", "memory"],
    "S144": ["unified", "theory", "synthesis", "integration", "holistic"]
}

class MetadataValidator:
    """Validates and enriches file metadata for RAG ingestion"""
    
    def __init__(self):
        self.required_fields = ["source", "sphere", "novelty", "category", "timestamp"]
        self.optional_fields = ["file_path", "word_count", "tags", "references"]
    
    def extract_frontmatter(self, file_path: str) -> Optional[Dict]:
        """
        Extract YAML frontmatter from markdown file.
        
        Supports formats:
        ---
        key: value
        ---
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    metadata = yaml.safe_load(frontmatter_text)
                    return metadata if isinstance(metadata, dict) else {}
            
            return {}
        
        except Exception as e:
            print(f"Warning: Could not extract frontmatter from {file_path}: {e}")
            return {}
    
    def auto_assign_sphere(self, file_path: str, content: str) -> Optional[str]:
        """
        Auto-assign sphere based on filename and content keywords.
        Returns best matching sphere or None.
        """
        text = (Path(file_path).stem + " " + content).lower()
        
        # Score each sphere based on keyword matches
        scores = {}
        for sphere, keywords in SPHERE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                scores[sphere] = score
        
        # Return highest scoring sphere
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    def count_words(self, content: str) -> int:
        """Count words in content"""
        # Remove markdown syntax
        text = re.sub(r'[#*`\[\]()]', '', content)
        words = text.split()
        return len(words)
    
    def validate_metadata(self, file_path: str, auto_enrich: bool = True) -> Dict:
        """
        Validate and enrich metadata for a file.
        
        Args:
            file_path: Path to the file
            auto_enrich: Automatically fill missing fields
        
        Returns:
            Complete validated metadata dict
        
        Raises:
            ValueError: If required fields are missing and can't be auto-filled
        """
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Could not read file {file_path}: {e}")
        
        # Extract frontmatter
        metadata = self.extract_frontmatter(file_path)
        
        # Auto-enrich if enabled
        if auto_enrich:
            # Source
            if "source" not in metadata:
                metadata["source"] = "sheldonbrain_os"  # Default source
            
            # Sphere
            if "sphere" not in metadata or metadata["sphere"] not in VALID_SPHERES:
                auto_sphere = self.auto_assign_sphere(file_path, content)
                if auto_sphere:
                    metadata["sphere"] = auto_sphere
                else:
                    metadata["sphere"] = "S144"  # Default to unified theory
            
            # Novelty
            if "novelty" not in metadata:
                # Estimate novelty based on content length and uniqueness
                word_count = self.count_words(content)
                if word_count > 5000:
                    metadata["novelty"] = 0.85
                elif word_count > 2000:
                    metadata["novelty"] = 0.75
                elif word_count > 500:
                    metadata["novelty"] = 0.65
                else:
                    metadata["novelty"] = 0.50
            
            # Category
            if "category" not in metadata:
                filename = Path(file_path).stem.lower()
                if "phd" in filename or "research" in filename:
                    metadata["category"] = "Research"
                elif "guide" in filename or "tutorial" in filename:
                    metadata["category"] = "Documentation"
                elif "manifesto" in filename or "theory" in filename:
                    metadata["category"] = "Theory"
                else:
                    metadata["category"] = "General"
            
            # Timestamp
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.utcnow().isoformat()
            
            # File path
            metadata["file_path"] = file_path
            
            # Word count
            metadata["word_count"] = self.count_words(content)
        
        # Validate required fields
        missing_fields = [f for f in self.required_fields if f not in metadata]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Validate sphere
        if metadata["sphere"] not in VALID_SPHERES:
            raise ValueError(f"Invalid sphere: {metadata['sphere']}")
        
        # Validate novelty
        try:
            novelty = float(metadata["novelty"])
            if not 0.0 <= novelty <= 1.0:
                raise ValueError(f"Novelty must be between 0.0 and 1.0, got {novelty}")
            metadata["novelty"] = novelty
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid novelty value: {metadata.get('novelty')}")
        
        return metadata
    
    def validate_batch(self, file_paths: List[str], auto_enrich: bool = True) -> Dict:
        """
        Validate a batch of files.
        
        Returns:
            {
                "valid": [(file_path, metadata), ...],
                "invalid": [(file_path, error), ...],
                "stats": {...}
            }
        """
        valid = []
        invalid = []
        
        for file_path in file_paths:
            try:
                metadata = self.validate_metadata(file_path, auto_enrich)
                valid.append((file_path, metadata))
            except Exception as e:
                invalid.append((file_path, str(e)))
        
        # Calculate stats
        spheres = {}
        categories = {}
        total_words = 0
        
        for _, metadata in valid:
            sphere = metadata.get("sphere", "Unknown")
            category = metadata.get("category", "Unknown")
            words = metadata.get("word_count", 0)
            
            spheres[sphere] = spheres.get(sphere, 0) + 1
            categories[category] = categories.get(category, 0) + 1
            total_words += words
        
        stats = {
            "total_files": len(file_paths),
            "valid_files": len(valid),
            "invalid_files": len(invalid),
            "success_rate": len(valid) / len(file_paths) if file_paths else 0,
            "total_words": total_words,
            "avg_words_per_file": total_words / len(valid) if valid else 0,
            "spheres": spheres,
            "categories": categories
        }
        
        return {
            "valid": valid,
            "invalid": invalid,
            "stats": stats
        }


def main():
    """Test the validator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 metadata_validator.py <file_or_directory>")
        sys.exit(1)
    
    path = sys.argv[1]
    validator = MetadataValidator()
    
    if os.path.isfile(path):
        # Validate single file
        try:
            metadata = validator.validate_metadata(path, auto_enrich=True)
            print("✅ Valid metadata:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
        except Exception as e:
            print(f"❌ Validation failed: {e}")
    
    elif os.path.isdir(path):
        # Validate directory
        file_paths = [
            os.path.join(path, f)
            for f in os.listdir(path)
            if f.endswith(('.md', '.txt'))
        ]
        
        print(f"🔍 Validating {len(file_paths)} files...")
        result = validator.validate_batch(file_paths, auto_enrich=True)
        
        print(f"\n📊 Results:")
        print(f"  Valid: {result['stats']['valid_files']}")
        print(f"  Invalid: {result['stats']['invalid_files']}")
        print(f"  Success rate: {result['stats']['success_rate']*100:.1f}%")
        print(f"  Total words: {result['stats']['total_words']:,}")
        print(f"  Avg words/file: {result['stats']['avg_words_per_file']:.0f}")
        
        print(f"\n📂 By Sphere:")
        for sphere, count in sorted(result['stats']['spheres'].items()):
            print(f"  {sphere}: {count}")
        
        print(f"\n📁 By Category:")
        for category, count in sorted(result['stats']['categories'].items()):
            print(f"  {category}: {count}")
        
        if result['invalid']:
            print(f"\n❌ Invalid files:")
            for file_path, error in result['invalid'][:10]:
                print(f"  {file_path}: {error}")
    
    else:
        print(f"❌ Path not found: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
