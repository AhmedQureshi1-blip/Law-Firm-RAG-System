"""
Day 2 CLI Test — Legal RAG Pipeline
Usage: python test_pipeline.py <path_to_pdf>

Runs the full ingestion pipeline and verifies the index is queryable.
"""

import sys
import uuid
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def run_test(pdf_path: str):
    from core.document_processor import extract_text_from_pdf, detect_special_flags
    from core.indexer import build_session_index, build_legal_corpus_index

    path = Path(pdf_path)
    if not path.exists():
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)

    session_id = str(uuid.uuid4())[:8]

    print("\n" + "=" * 60)
    print("  LEGAL RAG SYSTEM — DAY 2 PIPELINE TEST")
    print("=" * 60)
    print(f"  File      : {path.name}")
    print(f"  Session   : {session_id}")
    print("=" * 60 + "\n")

    # Step 1: Text extraction
    logger.info("STEP 1/5 — Extracting text from PDF...")
    pages = extract_text_from_pdf(str(path))
    urdu_pages = sum(1 for p in pages if p["is_urdu"])
    ocr_pages  = sum(1 for p in pages if p["has_ocr"])
    logger.info(f"  Total pages : {len(pages)}")
    logger.info(f"  Urdu pages  : {urdu_pages}")
    logger.info(f"  OCR pages   : {ocr_pages}")

    # Step 2: Flag detection
    logger.info("STEP 2/5 — Detecting Pakistani legal risk flags...")
    flags = detect_special_flags(pages)
    logger.info(f"  Inherited property  : {flags['is_inherited']}")
    logger.info(f"  Benami risk         : {flags['benami_risk']}")
    logger.info(f"  Contains Urdu       : {flags['has_urdu']}")

    # Step 3: Session index
    logger.info("STEP 3/5 — Building session index in ChromaDB...")
    session_index = build_session_index(pages, session_id)
    logger.info("  Session index built successfully.")

    # Step 4: Legal corpus index
    logger.info("STEP 4/5 — Loading Pakistani legal corpus index...")
    legal_index = build_legal_corpus_index()
    logger.info("  Legal corpus index ready.")

    # Step 5: Test query
    logger.info("STEP 5/5 — Running test query against session index...")

    import os
    groq_key = os.getenv("GROQ_API_KEY")

    if groq_key:
        from llama_index.llms.groq import Groq
        from llama_index.core import Settings
        Settings.llm = Groq(model="llama-3.3-70b-versatile", api_key=groq_key)
        logger.info("  LLM: Groq Llama 3.3 70B")
    else:
        logger.warning("  GROQ_API_KEY not set — retrieval-only mode (no synthesis)")

    query_engine = session_index.as_query_engine(similarity_top_k=3)
    test_query = (
        "What is the main subject of this document? "
        "Who are the parties involved and what property or matter is referenced?"
    )

    response = query_engine.query(test_query)

    print("\n" + "=" * 60)
    print("  PIPELINE TEST RESULTS")
    print("=" * 60)
    print(f"  Pages extracted : {len(pages)}")
    print(f"  Urdu pages      : {urdu_pages}")
    print(f"  OCR pages       : {ocr_pages}")
    print(f"  Flags           : {flags}")
    print("-" * 60)
    print("  Test Query:")
    print(f"  {test_query}")
    print("-" * 60)
    print("  Response:")
    print(f"  {response}")
    print("=" * 60)
    print("\n  ✅  PIPELINE TEST PASSED — index built and queryable.\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <path_to_pdf>")
        sys.exit(1)
    run_test(sys.argv[1])