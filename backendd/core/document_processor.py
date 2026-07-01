import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
from langdetect import detect
import logging
import re
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logger = logging.getLogger(__name__)

URDU_INDICATORS = [
    "واقع", "موضع", "مالک", "بیع", "خریدار", "فروخت",
    "قبضہ", "رجسٹری", "انتقال", "فرد", "مالکیت", "تحصیل"
]

INHERITED_INDICATORS = [
    "late", "deceased", "legal heirs of", "virasat",
    "succession", "inheritance", "marhoom", "warisan", "tarka"
]

BENAMI_INDICATORS = [
    "on behalf of", "beneficial owner", "in trust for",
    "nominee", "benamidar"
]

FBR_INDICATORS = [
    "consideration", "sale price", "purchase price",
    "total amount", "value of property", "rupees",
    "pkr", "rs.", "lakh", "crore"
]

AML_INDICATORS = [
    "source of funds", "beneficial owner", "payment receipt",
    "bank transfer", "demand draft", "pay order"
]

HOUSING_SOCIETY_PATTERNS = {
    "DHA Islamabad": ["dha islamabad", "defence housing authority islamabad"],
    "DHA Lahore": ["dha lahore", "defence housing authority lahore"],
    "Bahria Town Rawalpindi": ["bahria town rawalpindi", "bahria rawalpindi"],
    "Bahria Town Lahore": ["bahria town lahore", "bahria lahore"],
}

CONSTITUTIONAL_MAP = {
    "title": "Article 23 — Right to acquire and dispose of property",
    "noc": "Article 24 — Protection of property rights",
    "encumbrance": "Article 24 — Protection of property rights",
    "co-owner": "Article 25 — Equality of citizens",
    "litigation": "Article 24 — Protection of property rights",
    "ownerless": "Article 172 — Property vesting in Federal/Provincial government",
    "tax": "Article 23 — Right to acquire property subject to law",
}


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extract text page-by-page with OCR fallback for scanned pages.
    Returns list of page dicts with text and metadata.
    """
    pages = []
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            has_ocr = False

            # OCR fallback: trigger if extracted text is sparse
            if len(text.strip()) < 50:
                logger.info(f"Page {page_num}: sparse text detected, running OCR...")
                text = _ocr_page(pdf_path, page_num)
                has_ocr = True

            pages.append({
                "page_num": page_num,
                "text": text.strip(),
                "is_urdu": _detect_urdu(text),
                "has_ocr": has_ocr,
                "source_file": pdf_path.name,
            })

    return pages


def _ocr_page(pdf_path: Path, page_num: int) -> str:
    """Convert PDF page to image and run Tesseract OCR."""
    try:
        images = convert_from_path(
            pdf_path,
            first_page=page_num,
            last_page=page_num,
            dpi=300,
        )
        if images:
            try:
                # Urdu + English OCR
                return pytesseract.image_to_string(images[0], lang="urd+eng")
            except pytesseract.TesseractError:
                # Fallback to English if Urdu pack not installed
                logger.warning("Urdu Tesseract pack not found, falling back to English OCR.")
                return pytesseract.image_to_string(images[0], lang="eng")
    except Exception as e:
        logger.warning(f"OCR failed on page {page_num}: {e}")
    return ""


def _detect_urdu(text: str) -> bool:
    """Detect if page contains significant Urdu content."""
    if not text:
        return False
    if sum(1 for ind in URDU_INDICATORS if ind in text) >= 2:
        return True
    try:
        return detect(text) == "ur"
    except Exception:
        return False


def detect_special_flags(pages: list[dict]) -> dict:
    """
    Scan all pages for Pakistani-specific legal risk indicators.
    """
    full_text = " ".join(p["text"].lower() for p in pages)

    # Housing society detection
    detected_society = None
    for society, patterns in HOUSING_SOCIETY_PATTERNS.items():
        if any(p in full_text for p in patterns):
            detected_society = society
            break

    # Transaction value detection (rough PKR amount extraction)
    high_value = _detect_high_value_transaction(full_text)

    return {
        "is_inherited"      : any(ind in full_text for ind in INHERITED_INDICATORS),
        "benami_risk"       : any(ind in full_text for ind in BENAMI_INDICATORS),
        "has_urdu"          : any(p["is_urdu"] for p in pages),
        "has_ocr_pages"     : any(p["has_ocr"] for p in pages),
        "housing_society"   : detected_society,
        "high_value_txn"    : high_value["above_5m"],
        "aml_threshold"     : high_value["above_10m"],
        "fbr_applicable"    : high_value["above_5m"],
        "aml_indicators"    : any(ind in full_text for ind in AML_INDICATORS),
    }


def _detect_high_value_transaction(text: str) -> dict:
    """
    Detect whether transaction value exceeds PKR 5M (FBR threshold)
    or PKR 10M (AML threshold) using pattern matching.
    """
    import re

    # Match patterns like "50 lakh", "1 crore", "5,000,000", "PKR 7500000"
    lakh_pattern  = re.findall(r'(\d+(?:\.\d+)?)\s*lakh', text)
    crore_pattern = re.findall(r'(\d+(?:\.\d+)?)\s*crore', text)
    digit_pattern = re.findall(r'pkr\s*([\d,]+)|rs\.?\s*([\d,]+)', text)

    total_pkr = 0

    for val in lakh_pattern:
        total_pkr = max(total_pkr, float(val) * 100_000)

    for val in crore_pattern:
        total_pkr = max(total_pkr, float(val) * 10_000_000)

    for match in digit_pattern:
        raw = (match[0] or match[1]).replace(",", "")
        if raw.isdigit():
            total_pkr = max(total_pkr, int(raw))

    return {
        "above_5m" : total_pkr >= 5_000_000,
        "above_10m": total_pkr >= 10_000_000,
        "detected_value_pkr": total_pkr,
    }


def get_constitutional_basis(topic: str) -> str:
    """
    Return the relevant constitutional article for a given finding topic.
    Used by the query engine when building LLM prompts on Day 3.
    """
    topic_lower = topic.lower()
    for keyword, article in CONSTITUTIONAL_MAP.items():
        if keyword in topic_lower:
            return article
    return "Article 23 — Right to acquire and dispose of property"