"""Analytics Engine — the core "magic" of Kokoro Bot.

Takes a ``TranscriptionResult`` (raw Deepgram data) and produces a ``VibeReport``
with derived insights: vibe shifts, hot topics, consensus level, action items.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict

from kokoro.config import AnalyticsConfig
from kokoro.models import (
    ActionItem,
    ConsensusLevel,
    HotTopic,
    Sentiment,
    SentimentSegment,
    TopicEntry,
    TranscriptionResult,
    VibeReport,
    VibeShift,
)

logger = logging.getLogger(__name__)

# Intent keywords that signal an action / commitment
_ACTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(will|going to|need to|have to|must|should|plan to|commit to)\b", re.I),
    re.compile(r"\b(deliver|finish|complete|send|submit|prepare|schedule|fix|deploy)\b", re.I),
    re.compile(r"\b(action item|next step|follow.up|take.away)\b", re.I),
]

# Intent labels from Deepgram that hint at agreement / disagreement
_AFFIRMATION_KEYWORDS = {"affirm", "agree", "confirm", "approve", "accept", "yes", "affirmation"}
_DISAGREEMENT_KEYWORDS = {"disagree", "deny", "reject", "refuse", "oppose", "no", "disagreement"}


def _is_action_like(text: str) -> bool:
    return any(p.search(text) for p in _ACTION_PATTERNS)


def _classify_intent(intent_label: str) -> str | None:
    """Return 'affirm', 'disagree', or None."""
    lower = intent_label.lower()
    for kw in _AFFIRMATION_KEYWORDS:
        if kw in lower:
            return "affirm"
    for kw in _DISAGREEMENT_KEYWORDS:
        if kw in lower:
            return "disagree"
    return None


class Analyzer:
    """Transforms raw Deepgram output into a rich ``VibeReport``."""

    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self._cfg = config or AnalyticsConfig()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def analyze(self, result: TranscriptionResult) -> VibeReport:
        """Run the full analytics pipeline and return a ``VibeReport``."""
        report = VibeReport(
            summary=result.summary,
            transcript=result.transcript,
            overall_sentiment=result.sentiment_average_label,
            overall_sentiment_score=result.sentiment_average,
            sentiment_segments=result.sentiment_segments,
        )

        report.vibe_shifts = self._detect_vibe_shifts(result.sentiment_segments)
        report.hot_topics = self._detect_hot_topics(result)
        report.top_topics = self._collect_top_topics(result)
        report.action_items = self._extract_action_items(result)
        affirmation_ratio = self._compute_consensus(result)
        report.affirmation_ratio = affirmation_ratio
        report.consensus_level = self._ratio_to_level(affirmation_ratio)

        logger.info(
            "Analysis complete — %d vibe shifts, %d hot topics, %d actions, consensus=%s",
            len(report.vibe_shifts),
            len(report.hot_topics),
            len(report.action_items),
            report.consensus_level.value,
        )
        return report

    # ------------------------------------------------------------------
    # Vibe Shifts
    # ------------------------------------------------------------------

    def _detect_vibe_shifts(self, segments: list[SentimentSegment]) -> list[VibeShift]:
        """Find consecutive segments where sentiment delta exceeds the threshold."""
        shifts: list[VibeShift] = []
        for i in range(1, len(segments)):
            prev = segments[i - 1]
            curr = segments[i]
            delta = abs(curr.sentiment_score - prev.sentiment_score)
            if delta >= self._cfg.vibe_shift_threshold:
                shifts.append(
                    VibeShift(
                        timestamp_text=curr.text,
                        from_score=prev.sentiment_score,
                        to_score=curr.sentiment_score,
                        delta=delta,
                        from_sentiment=prev.sentiment,
                        to_sentiment=curr.sentiment,
                    )
                )
        return shifts

    # ------------------------------------------------------------------
    # Hot Topics (topics with the most negative sentiment)
    # ------------------------------------------------------------------

    def _detect_hot_topics(self, result: TranscriptionResult) -> list[HotTopic]:
        """Cross-reference topic segments with sentiment to find 'hot' topics."""
        # Build a mapping: word-index range → sentiment score
        word_sentiment: dict[tuple[int, int], SentimentSegment] = {}
        for seg in result.sentiment_segments:
            word_sentiment[(seg.start_word, seg.end_word)] = seg

        hot: list[HotTopic] = []
        for tseg in result.topic_segments:
            # Find the closest sentiment segment (overlapping word range)
            best_sent: SentimentSegment | None = None
            for (sw, ew), sseg in word_sentiment.items():
                if tseg.start_word <= ew and tseg.end_word >= sw:
                    if best_sent is None or sseg.sentiment_score < best_sent.sentiment_score:
                        best_sent = sseg
            if best_sent and best_sent.sentiment_score < self._cfg.negative_sentiment_threshold:
                for te in tseg.topics:
                    if te.confidence_score >= self._cfg.min_confidence:
                        hot.append(
                            HotTopic(
                                topic=te.topic,
                                sentiment_score=best_sent.sentiment_score,
                                sentiment=best_sent.sentiment,
                                context_text=tseg.text,
                            )
                        )
        # Deduplicate by topic name, keep lowest score
        seen: dict[str, HotTopic] = {}
        for h in hot:
            if h.topic not in seen or h.sentiment_score < seen[h.topic].sentiment_score:
                seen[h.topic] = h
        return sorted(seen.values(), key=lambda h: h.sentiment_score)

    # ------------------------------------------------------------------
    # Top Topics (all topics ranked by confidence)
    # ------------------------------------------------------------------

    def _collect_top_topics(self, result: TranscriptionResult) -> list[TopicEntry]:
        """Aggregate and rank all detected topics."""
        agg: dict[str, float] = defaultdict(float)
        for tseg in result.topic_segments:
            for te in tseg.topics:
                agg[te.topic] = max(agg[te.topic], te.confidence_score)
        entries = [TopicEntry(topic=t, confidence_score=s) for t, s in agg.items()]
        return sorted(entries, key=lambda e: e.confidence_score, reverse=True)[:10]

    # ------------------------------------------------------------------
    # Action Items
    # ------------------------------------------------------------------

    def _extract_action_items(self, result: TranscriptionResult) -> list[ActionItem]:
        """Extract intents that look like actions / commitments."""
        items: list[ActionItem] = []
        for iseg in result.intent_segments:
            for ie in iseg.intents:
                if _is_action_like(iseg.text) or _is_action_like(ie.intent):
                    items.append(
                        ActionItem(
                            text=iseg.text,
                            intent=ie.intent,
                            confidence=ie.confidence_score,
                        )
                    )
        return items

    # ------------------------------------------------------------------
    # Consensus (affirmation vs. disagreement ratio)
    # ------------------------------------------------------------------

    def _compute_consensus(self, result: TranscriptionResult) -> float:
        """Return the ratio of affirmation intents (0.0 – 1.0)."""
        affirm = 0
        total = 0
        for iseg in result.intent_segments:
            for ie in iseg.intents:
                cls = _classify_intent(ie.intent)
                if cls is not None:
                    total += 1
                    if cls == "affirm":
                        affirm += 1
        if total == 0:
            return 0.5  # No data → neutral
        return affirm / total

    @staticmethod
    def _ratio_to_level(ratio: float) -> ConsensusLevel:
        if ratio >= 0.70:
            return ConsensusLevel.HIGH
        if ratio >= 0.40:
            return ConsensusLevel.MODERATE
        return ConsensusLevel.LOW
