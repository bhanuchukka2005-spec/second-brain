"""
YouTube transcript downloader — compatible with youtube-transcript-api v2.x+
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
    Fetch YouTube transcript — works with both old and new API versions.
    Detects available methods at runtime so it never breaks on version changes.
    """
    try:
        import youtube_transcript_api as yta
    except ImportError:
        raise RuntimeError(
            "youtube-transcript-api not installed. "
            "Run: pip install youtube-transcript-api --upgrade"
        )

    video_id = extract_video_id(youtube_url)
    logger.info("Fetching transcript for video_id=%s", video_id)

    api_class = yta.YouTubeTranscriptApi
    full_text = ""

    # ── Strategy 1: v2.x new API (fetch() method on instance) ────────────────
    if hasattr(api_class, "fetch"):
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            fetched = YouTubeTranscriptApi.fetch(video_id)
            texts = []
            for seg in fetched:
                if isinstance(seg, dict):
                    texts.append(seg.get("text", ""))
                else:
                    texts.append(getattr(seg, "text", ""))
            full_text = " ".join(t for t in texts if t)
            logger.info("Used v2.x fetch() API")
        except Exception as e:
            raise RuntimeError(f"Could not fetch transcript: {e}")

    # ── Strategy 2: v1.x API (list_transcripts) ───────────────────────────────
    elif hasattr(api_class, "list_transcripts"):
        try:
            transcript_list = api_class.list_transcripts(video_id)
            transcript_obj = None
            try:
                transcript_obj = transcript_list.find_transcript(["en", "en-US", "en-GB"])
            except Exception:
                pass
            if transcript_obj is None:
                try:
                    transcript_obj = transcript_list.find_generated_transcript(["en"])
                except Exception:
                    pass
            if transcript_obj is None:
                all_t = list(transcript_list)
                if all_t:
                    transcript_obj = all_t[0]
            if transcript_obj is None:
                raise RuntimeError("No captions found for this video.")
            segments = transcript_obj.fetch()
            texts = []
            for seg in segments:
                if isinstance(seg, dict):
                    texts.append(seg.get("text", ""))
                else:
                    texts.append(getattr(seg, "text", ""))
            full_text = " ".join(t for t in texts if t)
            logger.info("Used v1.x list_transcripts() API")
        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Could not fetch transcript: {e}")

    # ── Strategy 3: oldest API (get_transcript) ───────────────────────────────
    elif hasattr(api_class, "get_transcript"):
        try:
            segments = api_class.get_transcript(video_id)
            full_text = " ".join(seg.get("text", "") for seg in segments)
            logger.info("Used legacy get_transcript() API")
        except Exception as e:
            raise RuntimeError(f"Could not fetch transcript: {e}")

    else:
        # Log available methods to help debug future version changes
        methods = [m for m in dir(api_class) if not m.startswith("_")]
        raise RuntimeError(
            f"Unsupported youtube-transcript-api version. "
            f"Available methods: {methods}. "
            "Run: pip install youtube-transcript-api --upgrade"
        )

    if not full_text.strip():
        raise RuntimeError(
            "No transcript content found. "
            "The video may not have captions enabled."
        )

    logger.info("Transcript words=%d", len(full_text.split()))

    # Chunk into 500-word segments
    source_label = f"YouTube: {youtube_url}"
    words = full_text.split()
    chunks = []
    chunk_size, overlap, i = 500, 50, 0
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