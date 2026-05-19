#!/usr/bin/env python3
"""Import matching audio from a local Anki package for private use.

This is intentionally separate from the Wikimedia downloader. The imported
deck may not provide redistribution rights, so this script marks imported
media as personal-use-only in media/audio_manifest.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import tempfile
import zipfile
from pathlib import Path

import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from build_deck import IPA_AUDIO_STEMS, MEDIA_DIR, MEDIA_MANIFEST_FIELDS, MEDIA_MANIFEST_PATH  # noqa: E402


SOURCE_URL = "https://ankiweb.net/shared/info/1963965925"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import exact IPA-symbol audio matches from a local .apkg for private use."
    )
    parser.add_argument("apkg", type=Path, help="source .apkg path")
    parser.add_argument("--overwrite", action="store_true", help="replace existing matching media files")
    return parser.parse_args()


def note_symbol(front: str) -> str:
    return re.split(r"[,<\s]", front.strip(), maxsplit=1)[0].strip()


def note_audio(back: str) -> str | None:
    match = re.search(r"\[sound:([^\]]+)\]", back)
    return match.group(1) if match else None


def load_manifest() -> dict[str, dict[str, str]]:
    if not MEDIA_MANIFEST_PATH.exists():
        return {}
    with MEDIA_MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            row["filename"]: {field: (row.get(field) or "") for field in MEDIA_MANIFEST_FIELDS}
            for row in csv.DictReader(file)
            if row.get("filename")
        }


def write_manifest(rows: dict[str, dict[str, str]]) -> None:
    with MEDIA_MANIFEST_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MEDIA_MANIFEST_FIELDS)
        writer.writeheader()
        for filename in sorted(rows):
            writer.writerow(rows[filename])


def import_row(filename: str, symbol: str, source_media: str) -> dict[str, str]:
    return {
        "filename": filename,
        "source_project": "Private AnkiWeb deck import",
        "source_title": f"IPA symbols and sounds: {symbol}",
        "source_url": SOURCE_URL,
        "author": "unknown AnkiWeb deck author",
        "license": "Unknown; personal use only",
        "license_url": SOURCE_URL,
        "notes": (
            "Imported from IPA_symbols_and_sounds.apkg for private local use only; "
            f"source media file was {source_media}. Do not redistribute without permission."
        ),
    }


def main() -> None:
    args = parse_args()
    if not args.apkg.exists():
        raise FileNotFoundError(args.apkg)

    MEDIA_DIR.mkdir(exist_ok=True)
    manifest = load_manifest()
    wanted = {
        ipa.strip("[]"): stem
        for ipa, stem in IPA_AUDIO_STEMS.items()
        if ipa.startswith("[") and ipa.endswith("]")
    }
    imported: list[str] = []
    skipped_existing: list[str] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        with zipfile.ZipFile(args.apkg) as package:
            package.extractall(temp)
        media_map = json.loads((temp / "media").read_text())
        media_id_by_name = {name: media_id for media_id, name in media_map.items()}
        db_path = temp / "collection.anki2"
        if not db_path.exists():
            db_path = temp / "collection.anki21"

        source_audio_by_symbol: dict[str, str] = {}
        conn = sqlite3.connect(db_path)
        try:
            for (fields,) in conn.execute("select flds from notes"):
                values = fields.split("\x1f")
                if len(values) < 2:
                    continue
                symbol = note_symbol(values[0])
                audio_name = note_audio(values[1])
                if symbol and audio_name and symbol not in source_audio_by_symbol:
                    source_audio_by_symbol[symbol] = audio_name
        finally:
            conn.close()

        for symbol, stem in sorted(wanted.items(), key=lambda item: item[1]):
            source_audio = source_audio_by_symbol.get(symbol)
            if not source_audio:
                continue
            media_id = media_id_by_name.get(source_audio)
            if media_id is None:
                continue
            target_name = f"mandarin_{stem}.mp3"
            target = MEDIA_DIR / target_name
            if target.exists() and not args.overwrite:
                skipped_existing.append(target_name)
                continue
            source_file = temp / media_id
            target.write_bytes(source_file.read_bytes())
            manifest[target_name] = import_row(target_name, symbol, source_audio)
            imported.append(f"{symbol} -> {target_name}")

    write_manifest(manifest)
    print(f"imported {len(imported)} file(s)")
    for line in imported:
        print(line)
    if skipped_existing:
        print(f"skipped existing {len(skipped_existing)} file(s); pass --overwrite to replace")


if __name__ == "__main__":
    main()
