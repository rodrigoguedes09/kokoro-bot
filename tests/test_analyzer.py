"""Unit tests for the Kokoro Analytics Engine."""

from kokoro.analyzer import Analyzer
from kokoro.config import AnalyticsConfig
from kokoro.models import (
    ConsensusLevel,
    IntentEntry,
    IntentSegment,
    Sentiment,
    SentimentSegment,
    TopicEntry,
    TopicSegment,
    TranscriptionResult,
)


def _make_sentiment_segments() -> list[SentimentSegment]:
    """Create sample sentiment segments with a clear vibe shift."""
    return [
        SentimentSegment(
            text="Hello everyone, welcome to the meeting.",
            start_word=0, end_word=6,
            sentiment=Sentiment.POSITIVE, sentiment_score=0.6,
        ),
        SentimentSegment(
            text="Let's discuss the project progress.",
            start_word=7, end_word=12,
            sentiment=Sentiment.NEUTRAL, sentiment_score=0.1,
        ),
        SentimentSegment(
            text="The deadline was missed and the client is upset.",
            start_word=13, end_word=22,
            sentiment=Sentiment.NEGATIVE, sentiment_score=-0.7,
        ),
        SentimentSegment(
            text="We need to fix this immediately.",
            start_word=23, end_word=29,
            sentiment=Sentiment.NEGATIVE, sentiment_score=-0.5,
        ),
    ]


def _make_result() -> TranscriptionResult:
    return TranscriptionResult(
        transcript="Hello everyone, welcome to the meeting. Let's discuss the project progress. The deadline was missed and the client is upset. We need to fix this immediately.",
        confidence=0.98,
        summary="Team meeting about a missed deadline. The client is upset and the team needs to fix the issue.",
        sentiment_segments=_make_sentiment_segments(),
        sentiment_average=-0.125,
        sentiment_average_label=Sentiment.NEUTRAL,
        topic_segments=[
            TopicSegment(
                text="The deadline was missed and the client is upset.",
                start_word=13, end_word=22,
                topics=[TopicEntry(topic="Missed deadline", confidence_score=0.85)],
            ),
        ],
        intent_segments=[
            IntentSegment(
                text="We need to fix this immediately.",
                start_word=23, end_word=29,
                intents=[IntentEntry(intent="Fix issue urgently", confidence_score=0.9)],
            ),
            IntentSegment(
                text="Yes I agree with the plan.",
                start_word=30, end_word=36,
                intents=[IntentEntry(intent="Affirmation", confidence_score=0.85)],
            ),
        ],
    )


class TestVibeShiftDetection:
    def test_detects_shift_between_positive_and_negative(self) -> None:
        analyzer = Analyzer(AnalyticsConfig(vibe_shift_threshold=0.4))
        result = _make_result()
        report = analyzer.analyze(result)

        # The jump from +0.1 → -0.7 (delta 0.8) should be detected
        assert len(report.vibe_shifts) >= 1
        shift = report.vibe_shifts[0]
        assert shift.delta >= 0.4

    def test_no_shift_when_threshold_high(self) -> None:
        analyzer = Analyzer(AnalyticsConfig(vibe_shift_threshold=5.0))
        result = _make_result()
        report = analyzer.analyze(result)
        assert len(report.vibe_shifts) == 0


class TestHotTopics:
    def test_detects_negative_topic(self) -> None:
        analyzer = Analyzer(AnalyticsConfig(negative_sentiment_threshold=-0.3))
        result = _make_result()
        report = analyzer.analyze(result)

        assert len(report.hot_topics) >= 1
        assert report.hot_topics[0].topic == "Missed deadline"

    def test_no_hot_topics_when_threshold_extreme(self) -> None:
        analyzer = Analyzer(AnalyticsConfig(negative_sentiment_threshold=-5.0))
        result = _make_result()
        report = analyzer.analyze(result)
        assert len(report.hot_topics) == 0


class TestConsensus:
    def test_consensus_with_affirmation(self) -> None:
        analyzer = Analyzer()
        result = _make_result()
        report = analyzer.analyze(result)

        # One affirmation intent out of 1 classifiable → 100 %
        assert report.affirmation_ratio == 1.0
        assert report.consensus_level == ConsensusLevel.HIGH


class TestActionItems:
    def test_detects_action_from_text(self) -> None:
        analyzer = Analyzer()
        result = _make_result()
        report = analyzer.analyze(result)

        # "We need to fix this immediately" matches the action pattern
        assert len(report.action_items) >= 1
        assert "fix" in report.action_items[0].text.lower()


class TestOverallReport:
    def test_summary_is_passed_through(self) -> None:
        analyzer = Analyzer()
        result = _make_result()
        report = analyzer.analyze(result)
        assert report.summary == result.summary

    def test_sentiment_segments_are_preserved(self) -> None:
        analyzer = Analyzer()
        result = _make_result()
        report = analyzer.analyze(result)
        assert len(report.sentiment_segments) == 4
