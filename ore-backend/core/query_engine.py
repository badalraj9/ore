import spacy
from nltk.corpus import wordnet
from typing import List, Dict, Any
import re

class QueryProcessor:
    def __init__(self):
        # Load Spacy model
        self.nlp = spacy.load("en_core_web_sm")

        # Scenario 6: Slang mapping
        self.slang_map = {
            "stuff": ["methods", "techniques", "models"],
            "med": ["medical"],
            "idk": [], # noise
            "cool": [], # noise
            "best ideas": [], # noise
        }

    def clean_query(self, query: str) -> str:
        """
        Cleans noise and maps slang.
        """
        tokens = query.split()
        cleaned = []
        for t in tokens:
            lower_t = t.lower()
            if lower_t in self.slang_map:
                mapped = self.slang_map[lower_t]
                if mapped:
                    cleaned.extend(mapped)
            else:
                cleaned.append(t)
        return " ".join(cleaned)

    def expand_query(self, query: str) -> List[str]:
        """
        Expands query terms using WordNet to find synonyms.
        """
        doc = self.nlp(query)
        expanded_terms = set()

        for token in doc:
            if token.pos_ in ["NOUN", "VERB"] and not token.is_stop:
                synonyms = set()
                for syn in wordnet.synsets(token.text):
                    for lemma in syn.lemmas():
                        synonyms.add(lemma.name().replace('_', ' '))
                # Add top 3 synonyms to avoid drift
                expanded_terms.update(list(synonyms)[:3])

        return sorted(list(expanded_terms)) # Sorted for determinism (Scenario 7)

    def extract_intent(self, query: str) -> str:
        """
        Rule-based intent classification.
        """
        query_lower = query.lower()
        if any(x in query_lower for x in ["compare", "difference", "vs", "versus"]):
            return "comparative_analysis"
        elif any(x in query_lower for x in ["overview", "survey", "review", "state of the art", "trend"]):
            return "literature_review"
        elif any(x in query_lower for x in ["method", "algorithm", "technique", "approach"]):
            return "methodology_search"
        else:
            return "general_search"

    def extract_entities(self, query: str) -> List[Dict[str, str]]:
        """
        Extracts entities using Spacy NER.
        """
        doc = self.nlp(query)
        entities = []
        for ent in doc.ents:
            entities.append({"text": ent.text, "label": ent.label_})
        return entities

    def process(self, query: str) -> Dict[str, Any]:
        """
        Main pipeline for query understanding.
        """
        # Scenario 10: Invalid Query
        if not query or not query.strip() or len(query) < 2:
            raise ValueError("invalid_query")

        # Scenario 8: Long query truncation (Basic implementation)
        # In a real system, we might summarize first. Here we truncate if excessively long (> 1000 chars)
        if len(query) > 1000:
             query = query[:1000]

        # Scenario 2 & 6: Clean
        clean_q = self.clean_query(query)

        intent = self.extract_intent(clean_q)
        entities = self.extract_entities(clean_q)
        expansion = self.expand_query(clean_q)

        # Keyword extraction
        keywords = [token.text for token in self.nlp(clean_q) if not token.is_stop and not token.is_punct]

        return {
            "original_query": query,
            "cleaned_query": clean_q,
            "intent": intent,
            "entities": entities,
            "keywords": keywords,
            "expanded_terms": expansion
        }

processor = QueryProcessor()
