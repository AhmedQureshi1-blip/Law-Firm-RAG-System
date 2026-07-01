import os
from llama_index.core import Settings
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.groq import Groq

GROQ_MODEL = "llama-3.3-70b-versatile"


def get_llm():
    return Groq(
        model=GROQ_MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
    )


def build_dual_engine(session_index, legal_corpus_index):
    """
    RouterQueryEngine querying both session documents and
    the Pakistani legal corpus simultaneously.
    Built on Day 3 — stub ready here.
    """
    llm = get_llm()
    Settings.llm = llm

    session_tool = QueryEngineTool.from_defaults(
        query_engine=session_index.as_query_engine(
            similarity_top_k=5, llm=llm
        ),
        description=(
            "Search the client's uploaded legal documents: "
            "sale deeds, title documents, NOCs, and other uploaded files."
        ),
    )

    corpus_tool = QueryEngineTool.from_defaults(
        query_engine=legal_corpus_index.as_query_engine(
            similarity_top_k=5, llm=llm
        ),
        description=(
            "Search Pakistani legal statutes: Constitution of Pakistan 1973, "
            "Transfer of Property Act 1882, Registration Act 1908, "
            "and all other Pakistani laws in the knowledge base."
        ),
    )

    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(llm=llm),
        query_engine_tools=[session_tool, corpus_tool],
        verbose=True,
    )