"""Discord bot integration for Kokoro.

Supports three modes of analysis:
  • /vibe-url   — analyse a remote audio URL
  • /vibe-file  — analyse an uploaded audio file
  • /join       — join the user's voice channel and start recording
  • /leave      — leave the voice channel, analyse the recording, and post the Vibe Report
"""

from __future__ import annotations

import asyncio
import io
import logging
import tempfile
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.voice_recv import VoiceRecvClient

from kokoro.analyzer import Analyzer
from kokoro.config import Settings
from kokoro.deepgram_client import KokoroDeepgramClient
from kokoro.report import (
    build_discord_embed_data,
    render_sentiment_chart,
    render_text,
)
from kokoro.voice_recorder import VoiceRecorder

logger = logging.getLogger(__name__)


class KokoroBot(commands.Bot):
    """Discord bot that analyses audio and posts Vibe Reports."""

    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self._dg = KokoroDeepgramClient(settings.deepgram)
        self._analyzer = Analyzer(settings.analytics)
        # guild_id → VoiceRecorder  (one recording per server)
        self._recorders: dict[int, VoiceRecorder] = {}

    async def setup_hook(self) -> None:
        self.tree.add_command(_analyze_file_cmd(self))
        self.tree.add_command(_analyze_url_cmd(self))
        self.tree.add_command(_join_cmd(self))
        self.tree.add_command(_leave_cmd(self))
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self) -> None:
        logger.info("Kokoro Bot is online as %s", self.user)


# ---------------------------------------------------------------------------
# Slash commands
# ---------------------------------------------------------------------------

def _analyze_url_cmd(bot: KokoroBot) -> app_commands.Command:
    @app_commands.command(name="vibe-url", description="Analyze audio from a URL and post the Vibe Report.")
    @app_commands.describe(url="Public URL of the audio file to analyze")
    async def vibe_url(interaction: discord.Interaction, url: str) -> None:
        await interaction.response.defer(thinking=True)
        try:
            result = await bot._dg.analyze_url(url)
            report = bot._analyzer.analyze(result)

            # Build embed
            embed_data = build_discord_embed_data(report)
            embed = discord.Embed(
                title=embed_data["title"],
                color=embed_data["color"],
            )
            for f in embed_data["fields"]:
                embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))

            # Attach chart
            chart_bytes = render_sentiment_chart(report)
            files: list[discord.File] = []
            if chart_bytes:
                files.append(discord.File(io.BytesIO(chart_bytes), filename="vibe_chart.png"))
                embed.set_image(url="attachment://vibe_chart.png")

            await interaction.followup.send(embed=embed, files=files)
        except Exception:
            logger.exception("Error in /vibe-url")
            await interaction.followup.send("❌ Something went wrong analysing that audio.", ephemeral=True)

    return vibe_url


def _analyze_file_cmd(bot: KokoroBot) -> app_commands.Command:
    @app_commands.command(name="vibe-file", description="Upload an audio file and get the Vibe Report.")
    @app_commands.describe(audio="The audio file to analyze")
    async def vibe_file(interaction: discord.Interaction, audio: discord.Attachment) -> None:
        await interaction.response.defer(thinking=True)
        try:
            # Download the attachment to a temp file
            with tempfile.NamedTemporaryFile(suffix=Path(audio.filename).suffix, delete=False) as tmp:
                await audio.save(tmp.name)  # type: ignore[arg-type]
                tmp_path = Path(tmp.name)

            result = await bot._dg.analyze_file(tmp_path)
            report = bot._analyzer.analyze(result)

            embed_data = build_discord_embed_data(report)
            embed = discord.Embed(
                title=embed_data["title"],
                color=embed_data["color"],
            )
            for f in embed_data["fields"]:
                embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))

            chart_bytes = render_sentiment_chart(report)
            files: list[discord.File] = []
            if chart_bytes:
                files.append(discord.File(io.BytesIO(chart_bytes), filename="vibe_chart.png"))
                embed.set_image(url="attachment://vibe_chart.png")

            await interaction.followup.send(embed=embed, files=files)
        except Exception:
            logger.exception("Error in /vibe-file")
            await interaction.followup.send("❌ Something went wrong analysing that audio.", ephemeral=True)
        finally:
            tmp_path.unlink(missing_ok=True)

    return vibe_file


# ---------------------------------------------------------------------------
# Voice channel commands — /join and /leave
# ---------------------------------------------------------------------------

async def _send_vibe_report(
    interaction: discord.Interaction,
    bot: KokoroBot,
    report: "VibeReport",  # noqa: F821
) -> None:
    """Build and send the Vibe Report embed (shared helper)."""
    embed_data = build_discord_embed_data(report)
    embed = discord.Embed(
        title=embed_data["title"],
        color=embed_data["color"],
    )
    for f in embed_data["fields"]:
        embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))

    chart_bytes = render_sentiment_chart(report)
    files: list[discord.File] = []
    if chart_bytes:
        files.append(discord.File(io.BytesIO(chart_bytes), filename="vibe_chart.png"))
        embed.set_image(url="attachment://vibe_chart.png")

    await interaction.followup.send(embed=embed, files=files)


def _join_cmd(bot: KokoroBot) -> app_commands.Command:
    @app_commands.command(
        name="join",
        description="Join your voice channel and start recording the conversation.",
    )
    async def join(interaction: discord.Interaction) -> None:
        # Ensure the user is in a voice channel
        if not interaction.user or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Could not determine your voice state.", ephemeral=True)
            return

        voice_state = interaction.user.voice
        if voice_state is None or voice_state.channel is None:
            await interaction.response.send_message(
                "❌ You need to be in a voice channel first!", ephemeral=True
            )
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command only works in a server.", ephemeral=True)
            return

        # Check if already recording in this guild
        if guild.id in bot._recorders and bot._recorders[guild.id].is_recording:
            await interaction.response.send_message(
                "⚠️ Already recording! Use `/leave` to stop and get the report.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        try:
            channel = voice_state.channel
            # Connect with VoiceRecvClient so we can receive audio
            vc: VoiceRecvClient = await channel.connect(cls=VoiceRecvClient)  # type: ignore[assignment]

            recorder = VoiceRecorder()
            recorder.start(vc)
            bot._recorders[guild.id] = recorder

            await interaction.followup.send(
                f"🎙️ Joined **{channel.name}** and recording!\n"
                f"Use `/leave` when the conversation is over to get the Vibe Report."
            )
        except Exception:
            logger.exception("Error in /join")
            await interaction.followup.send("❌ Failed to join the voice channel.", ephemeral=True)

    return join


def _leave_cmd(bot: KokoroBot) -> app_commands.Command:
    @app_commands.command(
        name="leave",
        description="Leave the voice channel, analyse the recording, and post the Vibe Report.",
    )
    async def leave(interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command only works in a server.", ephemeral=True)
            return

        recorder = bot._recorders.get(guild.id)
        if recorder is None or not recorder.is_recording:
            await interaction.response.send_message(
                "❌ I'm not recording in this server. Use `/join` first.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True)
        wav_path = None
        try:
            # Stop recording → get WAV file
            wav_path = await recorder.stop(output_dir=bot.settings.output_dir)
            bot._recorders.pop(guild.id, None)

            # Disconnect from voice
            if guild.voice_client:
                await guild.voice_client.disconnect(force=True)

            await interaction.followup.send("⏹️ Recording stopped. Analysing the conversation…")

            # Analyse with Deepgram
            result = await bot._dg.analyze_file(wav_path)
            report = bot._analyzer.analyze(result)

            # Send the report
            await _send_vibe_report(interaction, bot, report)

        except Exception:
            logger.exception("Error in /leave")
            await interaction.followup.send(
                "❌ Something went wrong processing the recording.", ephemeral=True
            )
        finally:
            # Clean up temp file
            if wav_path and wav_path.exists():
                wav_path.unlink(missing_ok=True)

    return leave


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_bot(settings: Settings) -> None:
    """Start the Discord bot (blocking call)."""
    if not settings.discord.bot_token:
        raise ValueError(
            "DISCORD_BOT_TOKEN is not set. "
            "Add it to your .env file or set the environment variable."
        )
    bot = KokoroBot(settings)
    bot.run(settings.discord.bot_token, log_handler=None)
