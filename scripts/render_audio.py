#!/usr/bin/env python3
"""Render PWA narration audio files with macOS say."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VOICE = "Miren (Enhanced)"
RATE = "185"


def main() -> None:
    audio_dir = ROOT / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    raw = (ROOT / "app" / "data.js").read_text(encoding="utf-8")
    payload = json.loads(raw.removeprefix("window.GUIDE_DATA = ").removesuffix(";\n"))
    for stop in payload["stops"]:
        stop_id = int(stop["id"])
        text = stop["speech"]
        mp4 = audio_dir / f"parada{stop_id:02d}.mp4"
        with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as handle:
            handle.write(text)
            script_path = Path(handle.name)
        try:
            subprocess.run(
                [
                    "/usr/bin/say",
                    "-v",
                    VOICE,
                    "-r",
                    RATE,
                    "-f",
                    str(script_path),
                    "--file-format=mp4f",
                    "-o",
                    str(mp4),
                ],
                check=True,
            )
        finally:
            script_path.unlink(missing_ok=True)
        print(f"Rendered {mp4.name}")


if __name__ == "__main__":
    main()
