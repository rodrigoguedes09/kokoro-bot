"""Domain models used across the Kokoro pipeline.

All models are plain dataclasses — no heavy dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ConsensusLevel(str, Enum):
    HIGH = "high"          # >=70 % affirmation intents
    MODERATE = "moderate"  # 40-69 %
    LOW = "low"            # <40 %


# ---------------------------------------------------------------------------
# Raw Deepgram results (thin wrappers for type safety)
# ---------------------------------------------------------------------------

@dataclass
class WordInfo:
    word: str
    start: float
    end: float
    confidence: float
    sentiment: Sentiment = Sentiment.NEUTRAL
    sentiment_score: float = 0.0
    speaker: int | None = None


@dataclass
class SentimentSegment:
    text: str
    start_word: int
    end_word: int
    sentiment: Sentiment
    sentiment_score: float


@dataclass
class TopicSegment:
    text: str
    start_word: int
    end_word: int
    topics: list[TopicEntry] = field(default_factory=list)


@dataclass
class TopicEntry:
    topic: str
    confidence_score: float


@dataclass
class IntentSegment:
    text: str
    start_word: int
    end_word: int
    intents: list[IntentEntry] = field(default_factory=list)


@dataclass
class IntentEntry:
    intent: str
    confidence_score: float


@dataclass
class TranscriptionResult:
    """All raw data returned by the Deepgram API for one audio source."""

    transcript: str = ""
    confidence: float = 0.0
    words: list[WordInfo] = field(default_factory=list)
    summary: str = ""
    sentiment_segments: list[SentimentSegment] = field(default_factory=list)
    sentiment_average: float = 0.0
    sentiment_average_label: Sentiment = Sentiment.NEUTRAL
    topic_segments: list[TopicSegment] = field(default_factory=list)
    intent_segments: list[IntentSegment] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Derived insights (produced by the Analytics Engine)
# ---------------------------------------------------------------------------

@dataclass
class VibeShift:
    """A moment where the sentiment changed drastically."""

    timestamp_text: str        # text of the segment where the shift happened
    from_score: float
    to_score: float
    delta: float               # absolute change
    from_sentiment: Sentiment
    to_sentiment: Sentiment


@dataclass
class HotTopic:
    """A topic associated with strong (usually negative) sentiment."""

    topic: str
    sentiment_score: float
    sentiment: Sentiment
    context_text: str


@dataclass
class ActionItem:
    """An intent that looks like an action/commitment."""

    text: str
    intent: str
    confidence: float


@dataclass
class VibeReport:
    """The final output — the 'magic information' delivered to the user."""

    # From Deepgram directly
    summary: str = ""
    transcript: str = ""

    # Overall vibe
    overall_sentiment: Sentiment = Sentiment.NEUTRAL
    overall_sentiment_score: float = 0.0

    # Derived insights
    vibe_shifts: list[VibeShift] = field(default_factory=list)
    hot_topics: list[HotTopic] = field(default_factory=list)
    action_items: list[ActionItem] = field(default_factory=list)
    top_topics: list[TopicEntry] = field(default_factory=list)

    # Consensus
    consensus_level: ConsensusLevel = ConsensusLevel.MODERATE
    affirmation_ratio: float = 0.0

    # Raw segments for charting
    sentiment_segments: list[SentimentSegment] = field(default_factory=list)
