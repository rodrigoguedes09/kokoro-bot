# 🎧 Kokoro Bot — The Vibe Architect

> Audio intelligence that reveals the **magic** hidden in conversations.

Kokoro listens to audio from the real world and delivers insights you didn't know you needed — hidden sentiments, unspoken tensions, overlooked topics, and pending action items.

Built with [Deepgram Audio Intelligence](https://developers.deepgram.com/docs/audio-intelligence) (Speech-to-Text, Sentiment Analysis, Intent Recognition, Topic Detection & Summarization).

---

## ✨ What It Does

| Feature | What Kokoro Reveals |
|---------|---------------------|
| **📊 Sentiment Timeline** | How the "vibe" evolved throughout the conversation |
| **⚡ Vibe Shifts** | Exact moments where the mood changed drastically |
| **🔥 Hot Topics** | Subjects that triggered negative or controversial reactions |
| **🤝 Consensus Index** | Whether people were agreeing or clashing |
| **✅ Action Items** | Commitments and next steps mentioned during the talk |
| **📝 TL;DR Summary** | AI-generated summary of the entire conversation |

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- A [Deepgram API key](https://console.deepgram.com/) (free tier available)

### 2. Install

```bash
git clone https://github.com/rodrigoguedes09/kokoro-bot.git
cd kokoro-bot
pip install -e .
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env and add your DEEPGRAM_API_KEY
```

### 4. Analyze Audio

```bash
# From a local file
python -m kokoro analyze --file meeting.wav

# From a URL
python -m kokoro analyze --url https://dpgr.am/spacewalk.wav

# Save report + chart to disk
python -m kokoro analyze --file meeting.wav --save
```

---

## 📖 Usage

### CLI Mode

```
🎧 Kokoro Bot — The Vibe Architect

positional arguments:
  {analyze,discord}
    analyze           Analyze an audio file or URL
    discord           Start the Discord bot

options:
  -v, --verbose       Enable debug logging
```

**Analyze subcommand:**

```
python -m kokoro analyze [-f FILE | -u URL] [-o OUTPUT_DIR] [-s]
```

| Flag | Description |
|------|-------------|
| `-f, --file` | Path to a local audio file (wav, mp3, etc.) |
| `-u, --url` | Public URL of an audio file |
| `-o, --output` | Output directory (default: `./output`) |
| `-s, --save` | Save JSON report and sentiment chart to disk |

### Discord Bot Mode

```bash
python -m kokoro discord
```

**Slash commands:**

| Command | Description |
|---------|-------------|
| `/vibe-url <url>` | Analyze audio from a URL |
| `/vibe-file <attachment>` | Upload an audio file for analysis |

---

## 🏗️ Architecture

```
Audio Source ──▶ Deepgram API ──▶ Analytics Engine ──▶ Report Generator
                 (STT + AI)       (Insights)           (Text + Chart)
```

### Project Structure

```
src/kokoro/
├── __main__.py          # CLI entry point
├── config.py            # Settings & environment variables
├── models.py            # Typed data models (dataclasses)
├── deepgram_client.py   # Deepgram API wrapper
├── analyzer.py          # Analytics engine (the "magic")
├── report.py            # Report generator (text, chart, JSON, Discord embed)
├── discord_bot.py       # Discord bot with slash commands
└── utils.py             # Helper functions
```

### Pipeline

1. **Input** → Audio file or URL
2. **Deepgram API** → Transcription + Sentiment + Topics + Intents + Summary
3. **Analytics Engine** → Vibe shifts, hot topics, consensus, action items
4. **Report Generator** → Terminal output, PNG chart, JSON export, Discord embed

---

## ⚙️ Configuration

All settings are loaded from environment variables (`.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPGRAM_API_KEY` | ✅ | — | Your Deepgram API key |
| `DISCORD_BOT_TOKEN` | Discord mode | — | Discord bot token |
| `DISCORD_REPORT_CHANNEL_ID` | Discord mode | — | Channel for reports |
| `VIBE_SHIFT_THRESHOLD` | No | `0.4` | Min sentiment delta to flag a vibe shift |
| `NEGATIVE_SENTIMENT_THRESHOLD` | No | `-0.3` | Threshold for "hot" topics |

---

## 🧪 Tests

```bash
pip install -e ".[dev]"
pytest
```

---

## ⚠️ Limitations

- Deepgram Audio Intelligence features work only for **English** audio
- Input token limit: **150K tokens** per request
- Sentiment analysis is segment-level (not real-time streaming)

---

## 📄 License

MIT
