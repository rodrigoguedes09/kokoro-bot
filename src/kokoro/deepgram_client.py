"""Deepgram API client — wraps the SDK v5 and returns typed domain models.

Supports both **local file** and **remote URL** audio sources.
"""

from __future__ import annotations

import logging
from pathlib import Path

from deepgram import AsyncDeepgramClient

from kokoro.config import DeepgramConfig
from kokoro.models import (
    IntentEntry,
    IntentSegment,
    Sentiment,
    SentimentSegment,
    TopicEntry,
    TopicSegment,
    TranscriptionResult,
    WordInfo,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers to parse the raw Deepgram JSON into typed dataclasses
# ---------------------------------------------------------------------------

def _parse_sentiment(raw: str) -> Sentiment:
    try:
        return Sentiment(raw.lower())
    except ValueError:
        return Sentiment.NEUTRAL


def _parse_words(words_raw: list[dict]) -> list[WordInfo]:
    out: list[WordInfo] = []
    for w in words_raw:
        out.append(
            WordInfo(
                word=w.get("punctuated_word", w.get("word", "")),
                start=w.get("start", 0.0),
                end=w.get("end", 0.0),
                confidence=w.get("confidence", 0.0),
                sentiment=_parse_sentiment(w.get("sentiment", "neutral")),
                sentiment_score=w.get("sentiment_score", 0.0),
                speaker=w.get("speaker"),
            )
        )
    return out


def _parse_sentiment_segments(data: dict) -> tuple[list[SentimentSegment], float, Sentiment]:
    sentiments = data.get("sentiments", {})
    if not sentiments:
        return [], 0.0, Sentiment.NEUTRAL
    segments: list[SentimentSegment] = []
    for seg in sentiments.get("segments", []):
        segments.append(
            SentimentSegment(
                text=seg.get("text", ""),
                start_word=seg.get("start_word", 0),
                end_word=seg.get("end_word", 0),
                sentiment=_parse_sentiment(seg.get("sentiment", "neutral")),
                sentiment_score=seg.get("sentiment_score", 0.0),
            )
        )
    avg = sentiments.get("average", {})
    avg_score = avg.get("sentiment_score", 0.0)
    avg_label = _parse_sentiment(avg.get("sentiment", "neutral"))
    return segments, avg_score, avg_label


def _parse_topic_segments(data: dict) -> list[TopicSegment]:
    topics = data.get("topics", {})
    if not topics:
        return []
    segments: list[TopicSegment] = []
    for seg in topics.get("segments", []):
        entries = [
            TopicEntry(topic=t.get("topic", ""), confidence_score=t.get("confidence_score", 0.0))
            for t in seg.get("topics", [])
        ]
        segments.append(
            TopicSegment(
                text=seg.get("text", ""),
                start_word=seg.get("start_word", 0),
                end_word=seg.get("end_word", 0),
                topics=entries,
            )
        )
    return segments


def _parse_intent_segments(data: dict) -> list[IntentSegment]:
    intents = data.get("intents", {})
    if not intents:
        return []
    segments: list[IntentSegment] = []
    for seg in intents.get("segments", []):
        entries = [
            IntentEntry(intent=i.get("intent", ""), confidence_score=i.get("confidence_score", 0.0))
            for i in seg.get("intents", [])
        ]
        segments.append(
            IntentSegment(
                text=seg.get("text", ""),
                start_word=seg.get("start_word", 0),
                end_word=seg.get("end_word", 0),
                intents=entries,
            )
        )
    return segments


def _build_options(cfg: DeepgramConfig) -> dict:
    """Return a dict of keyword arguments for the Deepgram SDK v5 transcribe methods."""
    return {
        "model": cfg.model,
        "language": cfg.language,
        "sentiment": cfg.sentiment,
        "intents": cfg.intents,
        "topics": cfg.topics,
        "summarize": cfg.summarize,
        "smart_format": cfg.smart_format,
        "diarize": cfg.diarize,
    }


def _result_to_dict(result: object) -> dict:
    """Convert SDK result to a plain dict regardless of the SDK version."""
    if hasattr(result, "to_dict"):
        return result.to_dict()  # type: ignore[union-attr]
    if hasattr(result, "model_dump"):
        return result.model_dump()  # type: ignore[union-attr]
    if isinstance(result, dict):
        return result
    # Fallback: try JSON round-trip
    import json as _json

    return _json.loads(str(result))


def _parse_response(raw: dict) -> TranscriptionResult:
    """Parse the raw Deepgram JSON into a ``TranscriptionResult``."""
    results = raw.get("results", {})

    # Transcript + words
    channels = results.get("channels", [])
    alt = {}
    if channels:
        alts = channels[0].get("alternatives", [])
        if alts:
            alt = alts[0]

    transcript = alt.get("transcript", "")
    confidence = alt.get("confidence", 0.0)
    words = _parse_words(alt.get("words", []))

    # Summary
    summary_obj = results.get("summary", {})
    summary = summary_obj.get("short", "") if summary_obj else ""

    # Sentiment
    sent_segs, sent_avg, sent_avg_label = _parse_sentiment_segments(results)

    # Topics
    topic_segs = _parse_topic_segments(results)

    # Intents
    intent_segs = _parse_intent_segments(results)

    return TranscriptionResult(
        transcript=transcript,
        confidence=confidence,
        words=words,
        summary=summary,
        sentiment_segments=sent_segs,
        sentiment_average=sent_avg,
        sentiment_average_label=sent_avg_label,
        topic_segments=topic_segs,
        intent_segments=intent_segs,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class KokoroDeepgramClient:
    """High-level async client that calls Deepgram and returns ``TranscriptionResult``."""

    def __init__(self, config: DeepgramConfig) -> None:
        if not config.api_key:
            raise ValueError(
                "DEEPGRAM_API_KEY is not set. "
                "Create a .env file (see .env.example) or set the environment variable."
            )
        self._config = config
        self._client = AsyncDeepgramClient(api_key=config.api_key)

    # ---- Local file -------------------------------------------------------

    async def analyze_file(self, file_path: str | Path) -> TranscriptionResult:
        """Transcribe + analyse a local audio file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        logger.info("Analyzing local file: %s", path)
        buffer = path.read_bytes()
        options = _build_options(self._config)

        response = await self._client.listen.v1.media.transcribe_file(
            request=buffer,
            **options,
        )
        raw = _result_to_dict(response)
        return _parse_response(raw)

    # ---- Remote URL -------------------------------------------------------

    async def analyze_url(self, url: str) -> TranscriptionResult:
        """Transcribe + analyse a remote audio file by URL."""
        logger.info("Analyzing remote URL: %s", url)
        options = _build_options(self._config)

        response = await self._client.listen.v1.media.transcribe_url(
            url=url,
            **options,
        )
        raw = _result_to_dict(response)
        return _parse_response(raw)
