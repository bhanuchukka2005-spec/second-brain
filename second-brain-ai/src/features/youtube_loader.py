"""
YouTube transcript downloader.
Supports youtu.be and youtube.com URL formats.
Compatible with youtube-transcript-api v1.0+
"""
import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str:
    """Extract video ID from any YouTube URL format."""
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
    raise ValueError(
        f"Could not extract video ID from URL: {url}\n"
        "Supported: https://youtu.be/XXX or https://youtube.com/watch?v=XXX"
    )


def fetch_transcript(youtube_url: str) -> List[dict]:
    """
    Fetches transcript using the new youtube-transcript-api v1.0+ API.
    Tries English first, then any available language.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError(
            "youtube-transcript-api not installed. "
            "Run: pip install youtube-transcript-api --upgrade"
        )

    video_id = extract_video_id(youtube_url)
    logger.info("Fetching transcript for video_id=%s", video_id)

    # v1.0+ uses YouTubeTranscriptApi().fetch() with a FetchedTranscript object
    # We try list_transcripts first to find the best available language
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except Exception as e:
        raise RuntimeError(
            f"Cannot access transcripts for this video.\n"
            f"It may be private, age-restricted, or unavailable.\nError: {e}"
        )

    # Try English manual → English auto-generated → any language
    transcript_obj = None

    try:
        transcript_obj = transcript_list.find_transcript(["en", "en-US", "en-GB"])
    except Exception:
        pass

    if transcript_obj is None:
        try:
            transcript_obj = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
        except Exception:
            pass

    if transcript_obj is None:
        try:
            all_transcripts = list(transcript_list)
            if all_transcripts:
                transcript_obj = all_transcripts[0]
                logger.info("Using non-English transcript: %s", transcript_obj.language)
        except Exception:
            pass

    if transcript_obj is None:
        raise RuntimeError(
            "No captions found for this video. "
            "The video must have captions (CC button on YouTube) to be indexed."
        )

    # Fetch the actual segments — works for both old and new API versions
    try:
        # New API (v1.0+): returns FetchedTranscript, iterate as list of dicts
        fetched = transcript_obj.fetch()
        # Handle both old dict format and new FetchedTranscript object format
        if hasattr(fetched, "__iter__"):
            segments = list(fetched)
            # Each segment may be a dict or a FetchedTranscriptSnippet object
            texts = []
            for seg in segments:
                if isinstance(seg, dict):
                    texts.append(seg.get("text", ""))
                else:
                    # New API returns objects with .text attribute
                    texts.append(getattr(seg, "text", str(seg)))
            full_text = " ".join(t for t in texts if t)
        else:
            full_text = str(fetched)
    except Exception as e:
        raise RuntimeError(f"Failed to download transcript content: {e}")

    if not full_text.strip():
        raise RuntimeError("Transcript is empty — cannot index this video.")

    logger.info(
        "Transcript fetched: video_id=%s words=%d",
        video_id, len(full_text.split())
    )

    # Chunk into 500-word segments with 50-word overlap
    source_label = f"YouTube: {youtube_url}"
    words = full_text.split()
    chunks = []
    chunk_size = 500
    overlap = 50
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append({"text": chunk, "source": source_label})
        i += chunk_size - overlap

    logger.info("Chunked into %d chunks", len(chunks))
    return chunks


def get_video_title(youtube_url: str) -> str:
    """Try to get video title for display purposes."""
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