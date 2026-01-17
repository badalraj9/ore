import sys
import os
import json
from sqlalchemy.orm import Session

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "ore-backend"))

from database import init_db, SessionLocal, Paper
from core.extraction.extractor import extractor
from config import settings

def test_extraction():
    # Initialize DB
    init_db()
    db = SessionLocal()

    # Get first paper
    paper = db.query(Paper).first()
    if not paper:
        print("No papers found in DB. Run test_phase2.py first.")
        return

    print(f"Testing extraction for: {paper.title} (ID: {paper.id})")

    # Run extraction
    if not paper.filepath_raw:
        print("Paper has no raw file.")
        return

    out_path = extractor.process(paper.filepath_raw, settings.PROCESSED_DIR)
    print(f"Extraction saved to: {out_path}")

    # Verify content
    with open(out_path, "r") as f:
        data = json.load(f)

    print("\n--- Extracted Sections ---")
    for section in data["sections"].keys():
        print(f"- {section}: {len(data['sections'][section])} chars")

    if "abstract" in data["sections"]:
        print("\n--- Abstract Snippet ---")
        print(data["sections"]["abstract"][:200] + "...")

    db.close()

if __name__ == "__main__":
    test_extraction()
