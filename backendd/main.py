import uuid
import os
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal RAG System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("./uploads")
OUTPUT_DIR = Path("./outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory session and status store
sessions: dict = {}
status_store: dict = {}


# ── Request/Response models ────────────────────────────────────────────
class QARequest(BaseModel):
    session_id: str
    question: str


# ── Endpoints ─────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "Legal RAG System API", "status": "running"}


@app.post("/api/upload")
async def upload_documents(
    files: list[UploadFile] = File(...),
    transaction_type: str = Form(default="property"),
    city: str = Form(default="islamabad"),
    housing_society: str = Form(default=""),
):
    session_id = str(uuid.uuid4())[:8]
    session_dir = UPLOAD_DIR / session_id
    session_dir.mkdir(exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"{file.filename} is not a PDF.")
        dest = session_dir / file.filename
        content = await file.read()
        dest.write_bytes(content)
        saved_files.append(str(dest))

    sessions[session_id] = {
        "files"            : saved_files,
        "transaction_type" : transaction_type,
        "city"             : city,
        "housing_society"  : housing_society,
    }
    status_store[session_id] = "uploaded"

    # Run pipeline in background
    import asyncio
    asyncio.create_task(_run_pipeline(session_id))

    return {"session_id": session_id, "files": len(saved_files)}


async def _run_pipeline(session_id: str):
    """Background pipeline: ingest → index → checklist → memo."""
    import asyncio
    try:
        info = sessions[session_id]

        from core.document_processor import (
            extract_text_from_pdf,
            detect_special_flags,
        )
        from core.indexer import build_session_index, build_legal_corpus_index
        from core.checklist import run_checklist
        from core.memo_generator import generate_memo

        # Step 1: Extract text
        status_store[session_id] = "processing"
        all_pages = []
        for pdf_path in info["files"]:
            pages = extract_text_from_pdf(pdf_path)
            all_pages.extend(pages)

        flags = detect_special_flags(all_pages)
        sessions[session_id]["flags"] = flags

        # Step 2: Build indexes
        status_store[session_id] = "indexing"
        session_index = await asyncio.to_thread(
            build_session_index, all_pages, session_id
        )
        legal_index = await asyncio.to_thread(build_legal_corpus_index)

        sessions[session_id]["session_index"] = session_index
        sessions[session_id]["legal_index"]   = legal_index

        # Step 3: Run checklist
        status_store[session_id] = "querying"
        results = await asyncio.to_thread(
            run_checklist,
            session_index,
            legal_index,
            info["transaction_type"],
            flags,
        )
        sessions[session_id]["results"] = results

        # Step 4: Generate memo
        status_store[session_id] = "generating"
        output_path = str(OUTPUT_DIR / f"{session_id}_memo.docx")
        doc_names = [Path(f).name for f in info["files"]]

        await asyncio.to_thread(
            generate_memo,
            results,
            output_path,
            "Law Firm",
            info["transaction_type"],
            info["city"],
            doc_names,
            flags,
        )
        sessions[session_id]["memo_path"] = output_path
        status_store[session_id] = "complete"
        logger.info(f"Pipeline complete for session {session_id}")

    except Exception as e:
        logger.error(f"Pipeline failed for {session_id}: {e}")
        status_store[session_id] = f"error: {str(e)}"


@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    status = status_store.get(session_id)
    if not status:
        raise HTTPException(404, "Session not found.")

    STAGE_MAP = {
        "uploaded"   : 10,
        "processing" : 25,
        "indexing"   : 45,
        "querying"   : 70,
        "generating" : 90,
        "complete"   : 100,
    }
    progress = STAGE_MAP.get(status, 0)
    if status.startswith("error"):
        progress = 0

    return {
        "session_id": session_id,
        "status"    : status,
        "progress"  : progress,
    }


@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found.")
    results = sessions[session_id].get("results")
    if not results:
        raise HTTPException(400, "Results not ready yet.")
    return results


@app.get("/api/download/{session_id}")
async def download_memo(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found.")
    memo_path = sessions[session_id].get("memo_path")
    if not memo_path or not Path(memo_path).exists():
        raise HTTPException(400, "Memo not ready yet.")
    return FileResponse(
        memo_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"due_diligence_memo_{session_id}.docx",
    )


@app.post("/api/query")
async def freeform_query(request: QARequest):
    session_id = request.session_id
    if session_id not in sessions:
        raise HTTPException(404, "Session not found.")

    session_index = sessions[session_id].get("session_index")
    legal_index   = sessions[session_id].get("legal_index")

    if not session_index or not legal_index:
        raise HTTPException(400, "Session index not ready. Upload documents first.")

    from core.checklist import run_freeform_query
    import asyncio

    result = await asyncio.to_thread(
        run_freeform_query,
        request.question,
        session_index,
        legal_index,
    )
    return result