#!/usr/bin/env python3
"""Localize one script into many languages with a single, consistent voice.

This mirrors the core localization use case: take a piece of content, render it
in every target language, and keep the same voice identity across all of them so
the brand sounds the same everywhere. It uses ElevenLabs' multilingual model so a
single voice can speak each language naturally.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

DEFAULT_MODEL = "eleven_multilingual_v2"
# "Rachel" — a stock ElevenLabs voice that works across languages.
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
OUTPUT_FORMAT = "mp3_44100_128"


def load_script(path):
    """Read a localized script file: a title plus a list of {language, code, text}."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("lines"), list) or not data["lines"]:
        raise ValueError('Script JSON must contain a non-empty "lines" array.')
    return data


def synthesize(client, text, voice_id, model_id):
    """Convert one line of text to speech and return the full audio as bytes."""
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=model_id,
        text=text,
        output_format=OUTPUT_FORMAT,
    )
    # The SDK streams the audio back as a generator of byte chunks.
    return b"".join(audio)


def main():
    parser = argparse.ArgumentParser(
        description="Localize a script into multiple languages with one ElevenLabs voice."
    )
    parser.add_argument("--script", default="script.json", help="Path to the localized script JSON.")
    parser.add_argument(
        "--voice-id",
        default=os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID),
        help="ElevenLabs voice ID to use for every language.",
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL, help="ElevenLabs model ID.")
    parser.add_argument("--out", default="output", help="Directory for the generated audio files.")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("Missing ELEVENLABS_API_KEY. Copy .env.example to .env and add your key.")

    client = ElevenLabs(api_key=api_key)
    script = load_script(args.script)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    title = script.get("title", "script")
    print(f'Localizing "{title}" into {len(script["lines"])} languages')
    print(f"Voice: {args.voice_id}  |  Model: {args.model_id}\n")

    for entry in script["lines"]:
        language = entry["language"]
        code = entry.get("code", language[:2].lower())
        text = entry["text"]

        print(f"  [{code}] {language}: {text}")
        audio = synthesize(client, text, args.voice_id, args.model_id)
        out_path = out_dir / f"{code}.mp3"
        out_path.write_bytes(audio)
        print(f"        -> {out_path} ({len(audio):,} bytes)\n")

    print("Done. Same voice, every language.")


if __name__ == "__main__":
    main()
