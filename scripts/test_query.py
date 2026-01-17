import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from core.query_engine import processor

def test_query():
    q = "What is the difference between Transformer and CNN for image classification?"
    print(f"Testing query: {q}")
    result = processor.process(q)
    print("Intent:", result["intent"])
    print("Entities:", result["entities"])
    print("Keywords:", result["keywords"])
    print("Expanded Terms:", result["expanded_terms"])

if __name__ == "__main__":
    test_query()
