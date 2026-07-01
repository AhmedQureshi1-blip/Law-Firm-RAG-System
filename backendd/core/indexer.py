import chromadb
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Document,
    Settings,
    SimpleDirectoryReader,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import logging

logger = logging.getLogger(__name__)

CHROMA_PATH = Path("./chroma_db")
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
LEGAL_CORPUS_COLLECTION = "legal_corpus_pk"


def _get_embed_model():
    return HuggingFaceEmbedding(model_name=EMBED_MODEL)


def _get_chroma_client():
    CHROMA_PATH.mkdir(exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def build_session_index(pages: list[dict], session_id: str) -> VectorStoreIndex:
    """
    Build a temporary per-upload index from extracted PDF pages.
    Collection name: session_{session_id}
    """
    Settings.embed_model = _get_embed_model()
    Settings.llm = None

    documents = [
        Document(
            text=p["text"],
            metadata={
                "page_num": p["page_num"],
                "source_file": p["source_file"],
                "is_urdu": p["is_urdu"],
                "has_ocr": p["has_ocr"],
                "session_id": session_id,
            },
        )
        for p in pages
        if p["text"].strip()
    ]

    chroma_client = _get_chroma_client()
    collection = chroma_client.get_or_create_collection(f"session_{session_id}")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    logger.info(
        f"Session index built: {len(documents)} chunks → "
        f"collection 'session_{session_id}'"
    )
    return index


def build_legal_corpus_index(
    corpus_dir: str = "./data/legal_corpus",
) -> VectorStoreIndex:
    """
    Build or load the persistent Pakistani legal statute index.
    First run indexes all PDFs in data/legal_corpus/.
    Subsequent runs load the existing ChromaDB collection instantly.
    """
    Settings.embed_model = _get_embed_model()
    Settings.llm = None

    chroma_client = _get_chroma_client()
    collection = chroma_client.get_or_create_collection(LEGAL_CORPUS_COLLECTION)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Already indexed — load and return immediately
    if collection.count() > 0:
        logger.info(
            f"Legal corpus already indexed ({collection.count()} chunks). "
            f"Loading existing index."
        )
        return VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
        )

    # First run — index PDFs from corpus directory
    corpus_path = Path(corpus_dir)
    pdf_files = list(corpus_path.glob("*.pdf")) if corpus_path.exists() else []

    if not pdf_files:
        logger.warning(
            "No PDFs in data/legal_corpus/ — "
            "add Pakistani statute PDFs and re-run. "
            "Returning empty index."
        )
        return VectorStoreIndex.from_documents(
            [],
            storage_context=storage_context,
        )

    logger.info(f"Building legal corpus index from {len(pdf_files)} PDFs...")
    reader = SimpleDirectoryReader(corpus_dir)
    documents = reader.load_data()

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )
    logger.info(f"Legal corpus indexed: {len(documents)} document chunks.")
    return index


def load_session_index(session_id: str) -> VectorStoreIndex:
    """Load an existing session index by session ID."""
    Settings.embed_model = _get_embed_model()
    Settings.llm = None

    chroma_client = _get_chroma_client()
    collection = chroma_client.get_or_create_collection(f"session_{session_id}")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )