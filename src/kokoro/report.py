"""Report generator — renders a ``VibeReport`` as terminal text and chart images."""

from __future__ import annotations

import io
import logging
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from kokoro.models import VibeReport
from kokoro.utils import ensure_dir, format_score, save_json, sentiment_emoji

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette for the sentiment chart
# ---------------------------------------------------------------------------
_COLORS = {
    "positive": "#4CAF50",
    "neutral": "#FFC107",
    "negative": "#F44336",
}


# ---------------------------------------------------------------------------
# Terminal text report
# ---------------------------------------------------------------------------

def render_text(report: VibeReport) -> str:
    """Return a multi-line string with the full Vibe Report."""
    lines: list[str] = []
    sep = "─" * 60

    lines.append("")
    lines.append(f"{'🎧 KOKORO — VIBE REPORT':^60}")
    lines.append(sep)

    # 1. Summary
    if report.summary:
        lines.append("")
        lines.append("📝 TL;DR")
        lines.append(report.summary)

    # 2. Overall sentiment
    lines.append("")
    lines.append("📊 Overall Vibe")
    emoji = sentiment_emoji(report.overall_sentiment_score)
    lines.append(
        f"   {emoji}  {report.overall_sentiment.value.capitalize()} "
        f"({format_score(report.overall_sentiment_score)})"
    )

    # 3. Vibe Shifts
    if report.vibe_shifts:
        lines.append("")
        lines.append(f"⚡ Vibe Shifts ({len(report.vibe_shifts)} detected)")
        for i, vs in enumerate(report.vibe_shifts, 1):
            lines.append(
                f"   {i}. {vs.from_sentiment.value} → {vs.to_sentiment.value} "
                f"(Δ {format_score(vs.delta)})"
            )
            snippet = vs.timestamp_text[:100] + ("…" if len(vs.timestamp_text) > 100 else "")
            lines.append(f"      \"{snippet}\"")

    # 4. Hot Topics
    if report.hot_topics:
        lines.append("")
        lines.append(f"🔥 Hot Topics (negative sentiment)")
        for ht in report.hot_topics:
            lines.append(
                f"   • {ht.topic} — sentiment {format_score(ht.sentiment_score)}"
            )

    # 5. Top Topics
    if report.top_topics:
        lines.append("")
        lines.append("🎯 Main Topics")
        for te in report.top_topics[:5]:
            lines.append(f"   • {te.topic} (confidence: {te.confidence_score:.2f})")

    # 6. Consensus
    lines.append("")
    lines.append("🤝 Consensus")
    lines.append(
        f"   Level: {report.consensus_level.value.capitalize()} "
        f"(affirmation ratio: {report.affirmation_ratio:.0%})"
    )

    # 7. Action Items
    if report.action_items:
        lines.append("")
        lines.append(f"✅ Action Items ({len(report.action_items)})")
        for ai in report.action_items:
            snippet = ai.text[:120] + ("…" if len(ai.text) > 120 else "")
            lines.append(f"   • [{ai.intent}] \"{snippet}\"")

    lines.append("")
    lines.append(sep)
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sentiment timeline chart (matplotlib)
# ---------------------------------------------------------------------------

def render_sentiment_chart(report: VibeReport, output_path: Path | None = None) -> bytes:
    """Generate a sentiment timeline chart and return PNG bytes.

    If *output_path* is given the chart is also saved to disk.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")  # headless backend
        import matplotlib.pyplot as plt
    except ImportError as exc:
        logger.warning("matplotlib not installed — skipping chart generation: %s", exc)
        return b""

    segments = report.sentiment_segments
    if not segments:
        logger.info("No sentiment segments — skipping chart.")
        return b""

    indices = list(range(len(segments)))
    scores = [s.sentiment_score for s in segments]
    colors = [_COLORS.get(s.sentiment.value, _COLORS["neutral"]) for s in segments]

    fig, ax = plt.subplots(figsize=(max(8, len(segments) * 0.6), 4))
    ax.bar(indices, scores, color=colors, edgecolor="white", linewidth=0.5)

    # Zero line
    ax.axhline(0, color="#888", linewidth=0.8, linestyle="--")

    # Mark vibe shifts with vertical lines
    shift_texts = {vs.timestamp_text for vs in report.vibe_shifts}
    for i, seg in enumerate(segments):
        if seg.text in shift_texts:
            ax.axvline(i, color="#9C27B0", linewidth=1.5, linestyle=":", alpha=0.7)

    ax.set_ylabel("Sentiment Score")
    ax.set_xlabel("Segment")
    ax.set_title("🎧 Kokoro — Sentiment Timeline")
    ax.set_ylim(-1.05, 1.05)
    ax.set_xticks(indices)
    ax.set_xticklabels([str(i + 1) for i in indices], fontsize=7)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    png_bytes = buf.getvalue()

    if output_path:
        ensure_dir(output_path.parent)
        output_path.write_bytes(png_bytes)
        logger.info("Chart saved to %s", output_path)

    return png_bytes


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def export_json(report: VibeReport, output_path: Path) -> Path:
    """Export the full VibeReport as a JSON file."""
    return save_json(asdict(report), output_path)


# ---------------------------------------------------------------------------
# Discord embed (dict for discord.py Embed construction)
# ---------------------------------------------------------------------------

def build_discord_embed_data(report: VibeReport) -> dict:
    """Return a dict ready to populate a ``discord.Embed``."""
    emoji = sentiment_emoji(report.overall_sentiment_score)
    fields: list[dict] = []

    # Summary
    if report.summary:
        fields.append({"name": "📝 TL;DR", "value": report.summary[:1024], "inline": False})

    # Overall
    fields.append({
        "name": "📊 Overall Vibe",
        "value": f"{emoji} {report.overall_sentiment.value.capitalize()} ({format_score(report.overall_sentiment_score)})",
        "inline": True,
    })

    # Consensus
    fields.append({
        "name": "🤝 Consensus",
        "value": f"{report.consensus_level.value.capitalize()} ({report.affirmation_ratio:.0%})",
        "inline": True,
    })

    # Vibe Shifts
    if report.vibe_shifts:
        shift_lines = []
        for vs in report.vibe_shifts[:3]:
            shift_lines.append(
                f"• {vs.from_sentiment.value} → {vs.to_sentiment.value} (Δ{format_score(vs.delta)})"
            )
        fields.append({"name": f"⚡ Vibe Shifts ({len(report.vibe_shifts)})", "value": "\n".join(shift_lines), "inline": False})

    # Hot Topics
    if report.hot_topics:
        ht_lines = [f"• {ht.topic} ({format_score(ht.sentiment_score)})" for ht in report.hot_topics[:5]]
        fields.append({"name": "🔥 Hot Topics", "value": "\n".join(ht_lines), "inline": False})

    # Action Items
    if report.action_items:
        ai_lines = [f"• {ai.intent}" for ai in report.action_items[:5]]
        fields.append({"name": f"✅ Action Items ({len(report.action_items)})", "value": "\n".join(ai_lines), "inline": False})

    return {
        "title": "🎧 Kokoro — Vibe Report",
        "color": 0x7C4DFF,
        "fields": fields,
    }
