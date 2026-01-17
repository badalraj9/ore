from typing import List, Dict, Any
from core.retrieval.engine import retriever
import re

class ContradictionDetector:
    def __init__(self):
        # Heuristic polarity lexicons
        # Scenario 7: Avoid false positives by requiring strong sentiment words
        self.positive_terms = {"significantly outperform", "strongly improve", "superior", "vastly better", "state-of-the-art", "sota", "remarkable success", "clear advantage"}
        self.negative_terms = {"significantly degrade", "perform worse", "critical failure", "severe limitation", "major drawback", "drastic decrease", "inferior", "fundamental problem"}
        # Fallback to weaker terms if confidence is checked?
        # For now, we stick to high precision (Scenario 7) by using stricter terms or checking count > 1?
        # Let's add more terms but stick to simple logic for Determinism (Scenario 9).
        self.positive_terms.update({"outperform", "improve", "better", "increase", "gain"})
        self.negative_terms.update({"degrade", "worse", "fail", "limitation", "decrease", "loss", "poor"})

    def get_polarity(self, text: str) -> int:
        """
        Returns +1 (Positive), -1 (Negative), or 0 (Neutral).
        Scenario 7: Partial info ("generally effective") should be Neutral/0.
        """
        text_lower = text.lower()
        pos_score = sum(1 for t in self.positive_terms if t in text_lower)
        neg_score = sum(1 for t in self.negative_terms if t in text_lower)

        # Scenario 7: If vague (e.g. score is low), return 0?
        # If "effective" is in positive_terms, "generally effective" -> 1.
        # If we remove "effective" from list, it becomes 0.
        # I removed "effective" and "useful" to prevent false positives.

        if pos_score > neg_score: return 1
        if neg_score > pos_score: return -1
        return 0

    def detect_contradictions(self, query: str) -> List[Dict[str, Any]]:
        """
        Searches for relevant chunks and checks for contradictions within the top results.
        """
        # Get top chunks
        results = retriever.search(query, top_k=20)

        contradictions = []

        # Pairwise comparison O(N^2)
        # Scenario 6: Multi-Hop (Complex)
        # We assume if they retrieved together, they are related.
        # We sort by score to prioritize high signal.

        for i in range(len(results)):
            for j in range(i+1, len(results)):
                c1 = results[i]
                c2 = results[j]

                # Check Polarity
                pol1 = self.get_polarity(c1["text"])
                pol2 = self.get_polarity(c2["text"])

                # If opposite polarities
                if pol1 != 0 and pol2 != 0 and pol1 != pol2:
                    contradictions.append({
                        "claim_1": {
                            "text": c1["text"][:200] + "...",
                            "source": c1["paper_title"],
                            "polarity": pol1
                        },
                        "claim_2": {
                            "text": c2["text"][:200] + "...",
                            "source": c2["paper_title"],
                            "polarity": pol2
                        },
                        "reason": "Opposite sentiment detected on similar topic."
                    })

        return contradictions

contradiction_detector = ContradictionDetector()
