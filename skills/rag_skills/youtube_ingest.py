import re
import subprocess
import tempfile
from pathlib import Path
from strands import tool
from ._chunker import chunk_text, generate_doc_id


def make_youtube_ingest_tool(collection, embedder):
    """Return a Strands @tool that downloads YouTube auto-captions and ingests them.

    Requires yt-dlp and ffmpeg to be installed in the container.
    Install via: pip install yt-dlp  and  apt-get install ffmpeg
    """

    @tool
    def youtube_ingest(video_url: str) -> str:
        """Download auto-generated captions from a YouTube video and ingest them into the knowledge base.

        Works with any YouTube URL (watch, shorts, playlist item).
        Captions are chunked and stored for future retrieval.

        Args:
            video_url: Full YouTube video URL.

        Returns:
            Summary of chunks ingested.
        """
        try:
            import yt_dlp  # noqa: F401  — presence check only
        except ImportError:
            return "Error: yt-dlp is not installed. Add it to this container's requirements."

        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = str(Path(tmpdir) / "%(id)s")
            result = subprocess.run(
                [
                    "yt-dlp",
                    "--write-auto-sub",
                    "--skip-download",
                    "--sub-format", "vtt",
                    "--sub-lang", "en",
                    "-o", out_template,
                    video_url,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                return f"yt-dlp failed for {video_url}:\n{result.stderr[:500]}"

            vtt_files = list(Path(tmpdir).glob("*.vtt"))
            if not vtt_files:
                return f"No English captions found for {video_url}. Try a video with auto-generated captions."

            text = _parse_vtt(vtt_files[0].read_text(encoding="utf-8"))
            video_id = vtt_files[0].stem.split(".")[0]

        doc_id = generate_doc_id(video_url)
        chunks = chunk_text(text, video_url, doc_id, "youtube", extra_meta={"video_id": video_id})
        _store_chunks(collection, embedder, chunks, doc_id)
        return f"Ingested {len(chunks)} chunks from YouTube video {video_url} (video_id={video_id})"

    return youtube_ingest


def _parse_vtt(vtt_text: str) -> str:
    """Strip VTT timestamps and deduplicate adjacent repeated lines."""
    lines = vtt_text.splitlines()
    text_lines: list[str] = []
    prev = ""
    for line in lines:
        # Skip header, timestamp lines, and blank lines
        if not line.strip() or line.startswith("WEBVTT") or re.match(r"^\d{2}:\d{2}", line) or "-->" in line:
            continue
        # Strip inline VTT tags like <00:00:01.000><c>
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean != prev:
            text_lines.append(clean)
            prev = clean
    return " ".join(text_lines)


def _store_chunks(collection, embedder, chunks: list[tuple[str, dict]], doc_id: str) -> None:
    if not chunks:
        return
    texts = [c[0] for c in chunks]
    metadatas = [c[1] for c in chunks]
    embeddings = [e.tolist() for e in embedder.embed(texts)]
    ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
    collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
