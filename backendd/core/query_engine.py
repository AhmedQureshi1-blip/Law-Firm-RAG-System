import os
from llama_index.core import Settings
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.groq import Groq

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert Pakistani legal due diligence assistant.
You analyze legal documents under Pakistani law including the Constitution of
Pakistan 1973, Transfer of Property Act 1882, Registration Act 1908,
Stamp Act 1899, Companies Act 2017, Muslim Family Laws Ordinance 1961,
Benami Transactions (Prohibition) Act 2017, and Anti-Money Laundering Act 2010.

For every question you are given, respond ONLY with a valid JSON object.
No preamble, no explanation outside the JSON. The JSON must follow this
exact schema:

{
  "question_id": <integer>,
  "question": "<the question asked>",
  "finding": "<what you found in the documents>",
  "reasoning": "<step-by-step legal reasoning — cite specific text found>",
  "document_citation": "<source file, page number, section if available>",
  "statutory_citation": "<relevant Pakistani statute and section>",
  "constitutional_basis": "<relevant Article of the Constitution of Pakistan 1973>",
  "risk_level": "<LOW or MEDIUM or HIGH>",
  "recommendation": "<specific actionable recommendation for the lawyer>",
  "missing_documents": ["<list any missing documents>"],
  "query_source": "<checklist or freeform>"
}

Rules:
- risk_level must be exactly LOW, MEDIUM, or HIGH
- If information is not found in the documents, state that clearly in finding
- Always cite the most specific Pakistani statute applicable
- Always map to the most relevant constitutional article
- missing_documents should be an empty list [] if nothing is missing
- Never invent information not present in the retrieved context
"""


def get_llm():
    return Groq(
        model=GROQ_MODEL,
        api_key=os.getenv("GROQ_API_KEY"),
        system_prompt=SYSTEM_PROMPT,
    )


def build_dual_engine(session_index, legal_corpus_index):
    """
    RouterQueryEngine querying both session documents
    and the Pakistani legal corpus simultaneously.
    """
    llm = get_llm()
    Settings.llm = llm

    session_tool = QueryEngineTool.from_defaults(
        query_engine=session_index.as_query_engine(
            similarity_top_k=3,
            llm=llm,
        ),
        description=(
            "Search the client's uploaded legal documents: "
            "sale deeds, title documents, NOCs, CNICs, "
            "tax receipts, and all other uploaded files."
        ),
    )

    corpus_tool = QueryEngineTool.from_defaults(
        query_engine=legal_corpus_index.as_query_engine(
            similarity_top_k=3,
            llm=llm,
        ),
        description=(
            "Search Pakistani legal statutes: Constitution of Pakistan 1973, "
            "Transfer of Property Act 1882, Registration Act 1908, "
            "Stamp Act 1899, Companies Act 2017, Muslim Family Laws "
            "Ordinance 1961, Benami Transactions Act 2017, "
            "Anti-Money Laundering Act 2010, and Income Tax Ordinance 2001."
        ),
    )

    return RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(llm=llm),
        query_engine_tools=[session_tool, corpus_tool],
        verbose=True,
    )


def build_session_only_engine(session_index):
    """
    Single-index engine for free-form Q&A when corpus
    context is not needed.
    """
    llm = get_llm()
    Settings.llm = llm
    return session_index.as_query_engine(
        similarity_top_k=5,
        llm=llm,
    )