import hashlib
import httpx
from bs4 import BeautifulSoup
import fitz  # pymupdf
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter


def generate_doc_id(source: str) -> str:
    """Stable 12-char doc ID derived from source name/URL."""
    return hashlib.md5(source.encode()).hexdigest()[:12]


def parse_pdf(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def parse_docx(content: bytes) -> str:
    import io
    docx = DocxDocument(io.BytesIO(content))
    return "\n".join(para.text for para in docx.paragraphs if para.text.strip())


def parse_text(content: bytes) -> str:
    return content.decode("utf-8", errors="replace")


def parse_url(url: str) -> str:
    response = httpx.get(url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def chunk_text(
    text: str,
    source: str,
    doc_id: str,
    file_type: str,
) -> list[tuple[str, dict]]:
    """Split text into chunks and return list of (chunk_text, metadata) tuples."""
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_text(text)
    return [
        (
            chunk,
            {
                "source_file": source,
                "chunk_index": i,
                "doc_id": doc_id,
                "file_type": file_type,
            },
        )
        for i, chunk in enumerate(chunks)
    ]
