import fitz  # PyMuPDF
import re
import json
import os
from typing import Dict, List, Any

class ContentExtractor:
    def __init__(self):
        # Regex patterns for common section headers
        self.section_patterns = {
            "abstract": re.compile(r"^\s*(?:abstract|summary)\s*$", re.IGNORECASE),
            "introduction": re.compile(r"^\s*(?:1\.?)?\s*introduction\s*$", re.IGNORECASE),
            "methods": re.compile(r"^\s*(?:\d+\.?)?\s*(?:methods|methodology|approach|proposed method)\s*$", re.IGNORECASE),
            "results": re.compile(r"^\s*(?:\d+\.?)?\s*(?:results|experiments|evaluation)\s*$", re.IGNORECASE),
            "discussion": re.compile(r"^\s*(?:\d+\.?)?\s*(?:discussion|limitations)\s*$", re.IGNORECASE),
            "conclusion": re.compile(r"^\s*(?:\d+\.?)?\s*(?:conclusion|conclusions)\s*$", re.IGNORECASE),
            "references": re.compile(r"^\s*(?:\d+\.?)?\s*references\s*$", re.IGNORECASE),
        }

    def extract_text_from_pdf(self, filepath: str) -> str:
        """
        Extracts raw text from PDF using PyMuPDF.
        """
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text

    def segment_sections(self, text: str) -> Dict[str, str]:
        """
        Segments text into canonical sections using heuristic matching.
        This is a simplified approach. Real-world PDFs are messy.
        """
        lines = text.split('\n')
        sections = {}
        current_section = "preamble"
        buffer = []

        for line in lines:
            clean_line = line.strip()
            # Check if line matches a header pattern
            matched_header = None
            for key, pattern in self.section_patterns.items():
                if pattern.match(clean_line):
                    matched_header = key
                    break

            if matched_header:
                # Save previous section
                if buffer:
                    sections[current_section] = "\n".join(buffer).strip()
                # Start new section
                current_section = matched_header
                buffer = []
            else:
                buffer.append(line)

        # Save last section
        if buffer:
            sections[current_section] = "\n".join(buffer).strip()

        return sections

    def process(self, filepath: str, output_dir: str) -> str:
        """
        Main extraction pipeline.
        Returns path to processed JSON.
        """
        filename = os.path.basename(filepath).replace(".pdf", ".json")
        output_path = os.path.join(output_dir, filename)

        # 1. Extract raw text
        raw_text = self.extract_text_from_pdf(filepath)

        # 2. Segment
        sections = self.segment_sections(raw_text)

        # 3. Construct payload
        data = {
            "source_file": filepath,
            "sections": sections,
            "raw_text_length": len(raw_text)
        }

        # 4. Save
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

extractor = ContentExtractor()
