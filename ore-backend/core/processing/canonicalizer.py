import re
import unicodedata
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from database import Entity, SessionLocal
import json
import spacy

class Canonicalizer:
    def __init__(self):
        # Regex for acronyms: "Convolutional Neural Network (CNN)"
        self.acronym_pattern = re.compile(r"([A-Z][a-zA-Z\s\-]+)\s\(([A-Z]+)\)")
        self.similarity_threshold = 0.85
        self.nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])

    def normalize(self, text: str) -> str:
        """
        Normalize text: NFKC, lowercase, strip.
        """
        text = unicodedata.normalize("NFKC", text)
        return text.strip()

    def lemmatize(self, text: str) -> str:
        """
        Scenario 6: Lemmatize term to avoid drift (Models -> Model).
        """
        doc = self.nlp(text)
        return " ".join([token.lemma_ for token in doc])

    def extract_acronyms(self, text: str):
        """
        Returns list of (full_name, acronym) tuples.
        """
        matches = self.acronym_pattern.findall(text)
        return [(m[0].strip(), m[1].strip()) for m in matches if len(m[1]) > 1]

    def link_entity(self, name: str, category: str = "General") -> str:
        """
        Links a surface name to a canonical entity ID (or creates one).
        """
        db = SessionLocal()
        try:
            # Scenario 6: Lemmatize before lookup
            lemma_name = self.lemmatize(name)
            norm_name = self.normalize(lemma_name).lower()

            existing = db.query(Entity).all()

            best_match = None
            best_score = 0.0

            for ent in existing:
                aliases = json.loads(ent.aliases)
                if norm_name in aliases:
                    return ent.canonical_name

                # Fuzzy match against canonical
                score = SequenceMatcher(None, norm_name, ent.canonical_name.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = ent

            if best_match and best_score >= self.similarity_threshold:
                # Add as alias if not present
                aliases = json.loads(best_match.aliases)
                if norm_name not in aliases:
                    aliases.append(norm_name)
                    best_match.aliases = json.dumps(aliases)
                    db.commit()
                return best_match.canonical_name

            # Create new
            # Use lemmatized name as canonical
            final_canonical = lemma_name.title() # Title case for display

            new_ent = Entity(
                canonical_name=final_canonical,
                aliases=json.dumps([norm_name]),
                category=category
            )
            db.add(new_ent)
            db.commit()
            return final_canonical

        finally:
            db.close()

    def process_chunk_entities(self, text: str):
        """
        Scans text for entities (Acronyms for now) and links them.
        """
        acronyms = self.extract_acronyms(text)
        for full, short in acronyms:
            # Link the full name first
            canonical = self.link_entity(full)
            # Link the acronym as an alias to the canonical
            self.register_alias(canonical, short)

    def register_alias(self, canonical: str, alias: str):
        db = SessionLocal()
        try:
            norm_can = self.normalize(canonical).lower()

            # Find entity
            ents = db.query(Entity).all()
            target = None
            for e in ents:
                if e.canonical_name == canonical or norm_can in json.loads(e.aliases):
                    target = e
                    break

            if not target:
                # Should have been created by link_entity, but fail-safe
                target = Entity(
                    canonical_name=canonical,
                    aliases=json.dumps([norm_can]),
                    category="General"
                )
                db.add(target)
                db.commit()
                db.refresh(target)

            # Add alias
            aliases = json.loads(target.aliases)
            if alias not in aliases:
                aliases.append(alias)
                target.aliases = json.dumps(aliases)
                db.commit()

        finally:
            db.close()

canonicalizer = Canonicalizer()
