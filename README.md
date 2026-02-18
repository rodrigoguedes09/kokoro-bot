# Kokoro Bot

Audio intelligence that transforms conversations into actionable insights.

Kokoro analyzes real-world audio to uncover hidden patterns: sentiment shifts, controversial topics, consensus levels, and action items that emerge during discussions. Built on Deepgram's Audio Intelligence API, it processes speech-to-text, sentiment analysis, intent recognition, and topic detection in a single pipeline.

## Features

**Sentiment Timeline** — Track how emotional tone evolves throughout the conversation with visual charts

**Vibe Shifts** — Identify exact moments where mood changed significantly (threshold-based detection)

**Hot Topics** — Flag subjects that triggered negative reactions or controversy

**Consensus Index** — Measure agreement levels based on affirmation patterns

**Action Items** — Extract commitments, decisions, and next steps from dialogue

**AI Summary** — Get a concise overview of the entire conversation

## Quick Start

### 1. Prerequisites

- Python 3.11+
**Prerequisites:** Python 3.11+ and a Deepgram API key (free tier available at console.deepgram.com)

**Installation:**s://github.com/rodrigoguedes09/kokoro-bot.git
cd kokoro-bot
pip install -e .
```

### 3. Configure
cp .env.example .env
```

Edit `.env` and add your `DEEPGRAM_API_KEY`.

**Basic Usage:**

```bash
# Analyze local file
python -m kokoro analyze --file meeting.wav

# Analyze remote URL
python -m kokoro analyze --url https://dpgr.am/spacewalk.wav

# Save report and chart to disk
python -m kokoro analyze --file meeting.wav --save
```

##
```
🎧 Kokoro Bot — The Vibe Architect

positional arguments:
  {analyze,discord}
    analyze           Analyze an audio file or URL
    discord           Start the Discord bot
ommand Line

```bash
python -m kokoro analyze [--file FILE | --url URL] [--output DIR] [--save]
```

Options:
- `--file, -f` — Path to local audio file (wav, mp3, flac, etc.)
- `--url, -u` — Public URL of audio file
- `--output, -o` — Output directory for reports (default: ./output)
- `--save, -s` — Save JSON report and sentiment chart to disk
- `--verbose, -v` — Enable debug logging

### Discord Bot

```bash
python -m kokoro discord
```

Configure `DISCORD_BOT_TOKEN` and `DISCORD_REPORT_CHANNEL_ID` in `.env` before running.

**Available Commands:**

`/vibe-url <url>` — Analyze audio from a public URL

`/vibe-file <attachment>` — Upload and analyze an audio file

`/join` — Join your current voice channel and start recording

`/leave` — Stop recording, analyze the conversation, and post a Vibe Report

##

The application follows a simple pipeline:

1. **Audio Input** — Local file, URL, or Discord voice channel recording
2. **Deepgram Processing** — Speech-to-text with sentiment, topics, intents, and summarization
3. **Analytics Engine** — Detection algorithms for vibe shifts, hot topics, consensus calculation, and action item extraction
4. **Report Generation** — Terminal output, sentiment timeline chart (PNG), JSON export, or Discord embed

**Core Components:**

- `deepgram_client.py` — Async wrapper for Deepgram SDK v5
- `analyzer.py` — Insight detection algorithms (vibe shifts use sentiment deltas above 0.4, hot topics cross-reference negative sentiment with detected topics)
- `report.py` — Multi-format output generation
- `voice_recorder.py` — Discord voice channel audio capture using discord-ext-voice-recv
- `discord_bot.py` — Bot with slash commands and voice recording capabilities

##nstall -e ".[dev]"
pytest
```

---

## ⚠️ Limitations

- Deepgram Audio Intelligence features work only for **English** audio
- Input token limit: **150K tokens** per request
- Sentiment analysis is segment-level (not real-time streaming)

---

## 📄 License
Environment variables (`.env` file):

**Required:**
- `DEEPGRAM_API_KEY` — Your Deepgram API key

**Discord Mode:**
- `DISCORD_BOT_TOKEN` — Bot token from Discord Developer Portal
- `DISCORD_REPORT_CHANNEL_ID` — Channel ID where reports will be posted

**Optional:**
- `VIBE_SHIFT_THRESHOLD` — Minimum sentiment delta to flag a vibe shift (default: 0.4)
- `NEGATIVE_SENTIMENT_THRESHOLD` — Sentiment threshold for hot topic detection (default: -0.3)

## Development

Run tests:
```bash
pip install -e ".[dev]"
pytest
```

The test suite includes 8 unit tests covering vibe shift detection, hot topic identification, consensus calculation, and action item extraction.

## Technical Details

**Audio Intelligence Features:** Deepgram API v5 with sentiment analysis, intent recognition, topic detection, speaker diarization, and v2 summarization

**Voice Recording:** 48kHz stereo 16-bit PCM capture from Discord voice channels, written to WAV format

**Sentiment Analysis:** Segment-level sentiment scores with timeline visualization using matplotlib

**Thresholds:** Vibe shifts detected when sentiment delta exceeds 0.4 between segments; topics flagged as "hot" when associated with sentiment below -0.3

## Limitations

- Audio Intelligence features currently support English audio only
- Maximum input length: 150,000 tokens per request
- Sentiment analysis operates on transcribed segments, not real-time streaming
- Voice recording requires PyNaCl and discord-ext-voice-recv extension

##
