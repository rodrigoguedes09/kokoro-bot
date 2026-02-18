"""CLI entry-point for Kokoro Bot.

Usage examples:

    # Analyse a local audio file
    python -m kokoro analyze --file meeting.wav

    # Analyse a remote URL
    python -m kokoro analyze --url https://example.com/audio.wav

    # Start the Discord bot
    python -m kokoro discord
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from kokoro.analyzer import Analyzer
from kokoro.config import load_settings
from kokoro.deepgram_client import KokoroDeepgramClient
from kokoro.report import export_json, render_sentiment_chart, render_text


def _setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

async def _cmd_analyze(args: argparse.Namespace) -> None:
    """Run audio analysis (CLI mode)."""
    settings = load_settings()
    dg = KokoroDeepgramClient(settings.deepgram)
    analyzer = Analyzer(settings.analytics)

    # Transcribe + analyse
    if args.file:
        result = await dg.analyze_file(args.file)
    elif args.url:
        result = await dg.analyze_url(args.url)
    else:
        print("Error: provide --file or --url", file=sys.stderr)
        sys.exit(1)

    report = analyzer.analyze(result)

    # Print text report
    print(render_text(report))

    # Save outputs if requested
    out_dir = Path(args.output) if args.output else settings.output_dir
    if args.save:
        out_dir.mkdir(parents=True, exist_ok=True)

        json_path = export_json(report, out_dir / "vibe_report.json")
        print(f"📄 JSON report saved to {json_path}")

        chart_path = out_dir / "sentiment_chart.png"
        png = render_sentiment_chart(report, chart_path)
        if png:
            print(f"📊 Sentiment chart saved to {chart_path}")


def _cmd_discord(_args: argparse.Namespace) -> None:
    """Start the Discord bot."""
    from kokoro.discord_bot import run_bot

    settings = load_settings()
    run_bot(settings)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kokoro",
        description="🎧 Kokoro Bot — The Vibe Architect. Audio intelligence that reveals the magic hidden in conversations.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    sub = parser.add_subparsers(dest="command")

    # ---- analyze ----------------------------------------------------------
    p_analyze = sub.add_parser("analyze", help="Analyze an audio file or URL")
    source = p_analyze.add_mutually_exclusive_group(required=True)
    source.add_argument("-f", "--file", type=str, help="Path to a local audio file")
    source.add_argument("-u", "--url", type=str, help="Public URL of an audio file")
    p_analyze.add_argument("-o", "--output", type=str, help="Output directory (default: ./output)")
    p_analyze.add_argument("-s", "--save", action="store_true", help="Save JSON report and chart to disk")

    # ---- discord ----------------------------------------------------------
    sub.add_parser("discord", help="Start the Discord bot")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    _setup_logging(args.verbose)

    if args.command == "analyze":
        asyncio.run(_cmd_analyze(args))
    elif args.command == "discord":
        _cmd_discord(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
