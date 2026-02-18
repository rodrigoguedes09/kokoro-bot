"""Configuration management for Kokoro Bot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from project root
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class DeepgramConfig:
    """Deepgram API configuration."""

    api_key: str = ""
    model: str = "nova-3"
    language: str = "en"
    sentiment: bool = True
    intents: bool = True
    topics: bool = True
    summarize: str = "v2"
    smart_format: bool = True
    diarize: bool = True


@dataclass(frozen=True)
class AnalyticsConfig:
    """Thresholds used by the Analytics Engine."""

    # Minimum absolute delta between consecutive sentiment segments to flag a "vibe shift"
    vibe_shift_threshold: float = 0.4
    # Sentiment score below which a segment is considered "negative"
    negative_sentiment_threshold: float = -0.3
    # Confidence floor — ignore results below this
    min_confidence: float = 0.3


@dataclass(frozen=True)
class DiscordConfig:
    """Discord bot configuration."""

    bot_token: str = ""
    report_channel_id: int = 0


@dataclass(frozen=True)
class Settings:
    """Top-level application settings — assembled from env vars."""

    deepgram: DeepgramConfig = field(default_factory=DeepgramConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    output_dir: Path = field(default_factory=lambda: Path("output"))


def load_settings() -> Settings:
    """Build a ``Settings`` instance from environment variables."""

    deepgram = DeepgramConfig(
        api_key=os.getenv("DEEPGRAM_API_KEY", ""),
        model=os.getenv("DEEPGRAM_MODEL", "nova-3"),
        language=os.getenv("DEEPGRAM_LANGUAGE", "en"),
    )

    analytics = AnalyticsConfig(
        vibe_shift_threshold=float(os.getenv("VIBE_SHIFT_THRESHOLD", "0.4")),
        negative_sentiment_threshold=float(
            os.getenv("NEGATIVE_SENTIMENT_THRESHOLD", "-0.3")
        ),
    )

    discord = DiscordConfig(
        bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
        report_channel_id=int(os.getenv("DISCORD_REPORT_CHANNEL_ID", "0")),
    )

    output_dir = Path(os.getenv("KOKORO_OUTPUT_DIR", "output"))

    return Settings(
        deepgram=deepgram,
        analytics=analytics,
        discord=discord,
        output_dir=output_dir,
    )
