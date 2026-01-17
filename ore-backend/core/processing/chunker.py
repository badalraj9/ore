import spacy
import json
import re
import unicodedata
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from database import Chunk, Paper, SessionLocal

class SectionAwareChunker:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        self.nlp.add_pipe("sentencizer")

        # Configuration rules: (target_tokens, overlap_tokens)
        self.rules = {
            "abstract": (400, 0), # Keep whole if possible
            "introduction": (350, 40),
            "methods": (400, 40),
            "results": (500, 50),
            "discussion": (400, 40),
            "conclusion": (350, 40),
            "default": (300, 30)
        }

    def clean_text(self, text: str) -> str:
        """
        Scenario 2: Clean noisy text.
        """
        if not text: return ""

        # 1. Normalize Unicode (fi -> fi, etc)
        text = unicodedata.normalize("NFKC", text)

        # 2. Replace LaTeX math/citations with placeholders (Simple regex)
        # Remove citation markers [1], [1-3], (Smith, 2020)
        text = re.sub(r"\[\d+(?:-\d+)?\]", "", text)

        # 3. Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # 4. Remove control chars
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch == " ")

        return text

    def chunk_text(self, text: str, target_size: int, overlap: int) -> List[str]:
        """
        Splits text into chunks respecting sentence boundaries.
        Scenario 9: Handles overflow by splitting sentences if needed (fallback).
        """
        cleaned_text = self.clean_text(text)
        doc = self.nlp(cleaned_text)
        sentences = [sent.text.strip() for sent in doc.sents]

        chunks = []
        current_chunk = []
        current_count = 0

        i = 0
        while i < len(sentences):
            sent = sentences[i]
            sent_len = len(sent.split())

            # Scenario 9: Extreme length sentence check
            if sent_len > target_size:
                # Flush current
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = []
                    current_count = 0

                # Split large sentence arbitrarily by words
                words = sent.split()
                for k in range(0, len(words), target_size - overlap):
                    sub_sent = " ".join(words[k : k + target_size])
                    chunks.append(sub_sent)
                i += 1
                continue

            # Standard Logic
            if current_count + sent_len > target_size and current_chunk:
                # Flush current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Handle overlap
                backtrack_tokens = 0
                backtrack_idx = len(current_chunk) # Default to no overlap if sentence is huge

                # Find overlap point from end
                for j in range(len(current_chunk)-1, -1, -1):
                    backtrack_tokens += len(current_chunk[j].split())
                    if backtrack_tokens >= overlap:
                        backtrack_idx = j
                        break

                # New chunk starts with overlap sentences
                current_chunk = current_chunk[backtrack_idx:]
                current_count = sum(len(s.split()) for s in current_chunk)

            current_chunk.append(sent)
            current_count += sent_len
            i += 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def process_paper(self, paper_id: int):
        """
        Reads processed JSON, chunks it, saves to DB.
        """
        db = SessionLocal()
        try:
            paper = db.query(Paper).filter(Paper.id == paper_id).first()
            if not paper or not paper.filepath_processed:
                # print(f"Paper {paper_id} not processed yet.")
                return

            with open(paper.filepath_processed, "r") as f:
                data = json.load(f)

            sections = data.get("sections", {})

            # Clear old chunks for idempotency (Scenario 8: Determinism)
            db.query(Chunk).filter(Chunk.paper_id == paper_id).delete()

            # Sort keys for deterministic order
            sorted_sections = sorted(sections.keys())

            for section_name in sorted_sections:
                content = sections[section_name]
                rule_name = section_name.lower()

                # Heuristic mapping for section names
                if "method" in rule_name: rule_name = "methods"
                elif "result" in rule_name: rule_name = "results"
                elif "discuss" in rule_name: rule_name = "discussion"
                elif "intro" in rule_name: rule_name = "introduction"
                elif "conc" in rule_name: rule_name = "conclusion"
                elif "abs" in rule_name: rule_name = "abstract"

                target, overlap = self.rules.get(rule_name, self.rules["default"])

                # Special case: Abstract (keep whole if small enough)
                if rule_name == "abstract" and len(content.split()) <= target:
                    text_chunks = [self.clean_text(content)]
                else:
                    text_chunks = self.chunk_text(content, target, overlap)

                for txt in text_chunks:
                    if not txt.strip(): continue # Skip empty chunks
                    chunk = Chunk(
                        paper_id=paper_id,
                        section=section_name,
                        text=txt,
                        token_count=len(txt.split())
                    )
                    db.add(chunk)

            db.commit()
            # print(f"Chunking complete for Paper {paper_id}")

        finally:
            db.close()

chunker = SectionAwareChunker()
