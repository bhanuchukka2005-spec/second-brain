"""
YouTube transcript downloader.
Compatible with youtube-transcript-api v2.x (methods: fetch, list).
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    patterns = [
        r"youtu\.be/([0-9A-Za-z_-]{11})",
        r"youtube\.com/watch\?v=([0-9A-Za-z_-]{11})",
        r"youtube\.com/embed/([0-9A-Za-z_-]{11})",
        r"youtube\.com/shorts/([0-9A-Za-z_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Cannot extract video ID from: {url}")


def fetch_transcript(youtube_url: str) -> List[dict]:
    """
    Fetch YouTube transcript using v2.x API.
    v2.x: instantiate the class, then call .fetch(video_id) on the instance.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError(
            "youtube-transcript-api not installed. "
            "Run: pip install youtube-transcript-api"
        )

    video_id = extract_video_id(youtube_url)
    logger.info("Fetching transcript for video_id=%s", video_id)

    # v2.x: create an instance first, then call fetch
    ytt = YouTubeTranscriptApi()

    try:
        fetched = ytt.fetch(video_id)
    except Exception as e:
        err = str(e).lower()
        if "no element found" in err or "could not retrieve" in err:
            raise RuntimeError(
                "No captions found for this video. "
                "Make sure the video has CC/subtitles enabled on YouTube."
            )
        raise RuntimeError(
            f"Could not fetch transcript: {e}\n"
            "The video may be private, age-restricted, or have no captions."
        )

    # Extract text from segments (handles both dict and object formats)
    texts = []
    for seg in fetched:
        if isinstance(seg, dict):
            texts.append(seg.get("text", ""))
        else:
            texts.append(getattr(seg, "text", str(seg)))

    full_text = " ".join(t for t in texts if t.strip())

    if not full_text.strip():
        raise RuntimeError("Transcript is empty — cannot index this video.")

    logger.info("Transcript fetched: words=%d", len(full_text.split()))

    # Chunk into 500-word segments with 50-word overlap
    source_label = f"YouTube: {youtube_url}"
    words = full_text.split()
    chunks, chunk_size, overlap, i = [], 500, 50, 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append({"text": chunk, "source": source_label})
        i += chunk_size - overlap

    logger.info("Chunked into %d chunks", len(chunks))
    return chunks


def get_video_title(youtube_url: str) -> str:
    import urllib.request
    import json as _json
    try:
        video_id = extract_video_id(youtube_url)
        url = (
            "https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )
        with urllib.request.urlopen(url, timeout=5) as r:
            data = _json.loads(r.read())
            return str(data.get("title", video_id))
    except Exception:
        return youtube_url
