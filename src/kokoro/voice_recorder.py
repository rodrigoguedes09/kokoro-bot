"""Voice recording module — captures audio from a Discord voice channel.

Uses ``discord-ext-voice-recv`` to receive decoded PCM from all speakers,
mixes them into a single WAV file, and returns the path for analysis.
"""

from __future__ import annotations

import io
import logging
import struct
import tempfile
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from discord.ext.voice_recv import BasicSink, VoiceData, VoiceRecvClient

if TYPE_CHECKING:
    import discord

logger = logging.getLogger(__name__)

# Discord voice settings (48 kHz, stereo, 16-bit signed LE)
SAMPLE_RATE = 48_000
CHANNELS = 2
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes


class VoiceRecorder:
    """Records all incoming voice in a channel into a single WAV buffer.

    Usage::

        recorder = VoiceRecorder()
        recorder.start(voice_client)   # voice_client must be VoiceRecvClient
        # ... wait for the meeting to finish ...
        wav_path = await recorder.stop()   # returns Path to the .wav file
    """

    def __init__(self) -> None:
        self._buffer = io.BytesIO()
        self._recording = False
        self._voice_client: VoiceRecvClient | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    # ------------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------------

    def start(self, voice_client: VoiceRecvClient) -> None:
        """Begin listening on *voice_client*."""
        if self._recording:
            raise RuntimeError("Already recording.")

        self._buffer = io.BytesIO()
        self._recording = True
        self._voice_client = voice_client

        sink = BasicSink(self._on_audio)
        voice_client.listen(sink)
        logger.info("🎙️ Recording started.")

    async def stop(self, output_dir: Path | None = None) -> Path:
        """Stop recording and write the WAV file to disk.

        Returns the ``Path`` to the WAV file.
        """
        if not self._recording or self._voice_client is None:
            raise RuntimeError("Not currently recording.")

        self._voice_client.stop_listening()
        self._recording = False
        logger.info("⏹️ Recording stopped. Flushing WAV …")

        wav_path = self._flush_wav(output_dir)
        logger.info("💾 WAV saved: %s (%.1f KB)", wav_path, wav_path.stat().st_size / 1024)
        return wav_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_audio(self, user: discord.Member | discord.User | None, data: VoiceData) -> None:
        """Callback invoked for each decoded audio packet."""
        if data.pcm is not None:
            self._buffer.write(data.pcm)

    def _flush_wav(self, output_dir: Path | None = None) -> Path:
        """Wrap the raw PCM buffer in a WAV container and save to disk."""
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            fd = tempfile.NamedTemporaryFile(
                suffix=".wav", dir=output_dir, delete=False
            )
        else:
            fd = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

        wav_path = Path(fd.name)
        pcm_data = self._buffer.getvalue()

        with wave.open(fd, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(SAMPLE_WIDTH)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm_data)

        self._buffer = io.BytesIO()
        return wav_path
