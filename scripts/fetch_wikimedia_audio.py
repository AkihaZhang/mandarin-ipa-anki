#!/usr/bin/env python3
"""Fetch direct Wikimedia IPA/phonetic samples and transcode them to MP3.

This script is intentionally direct-only: it does not concatenate phoneme
pieces, synthesize tones, create silence placeholders, or download Mandarin
example-word recordings. It overlays direct IPA samples onto the existing
media manifest, so pinyin syllable demos can remain as fallback audio for
items with no suitable direct sample.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from build_deck import MEDIA_DIR, MEDIA_MANIFEST_FIELDS  # noqa: E402


MANIFEST_PATH = MEDIA_DIR / "audio_manifest.csv"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "Chinese-IPA-Anki/0.3 direct-only audio fetcher"


AUTHOR_OVERRIDES = {
    "File:Voiceless bilabial plosive.ogg": "Peter Isotalo",
    "File:Aspirated voiceless bilabial stop.ogg": "joni",
    "File:Voiceless alveolar plosive.ogg": "Peter Isotalo",
    "File:Aspirated voiceless alveolar stop.ogg": "joni",
    "File:Voiceless velar plosive.ogg": "Peter Isotalo",
    "File:Bilabial nasal.ogg": "Peter Isotalo",
    "File:Alveolar nasal.ogg": "Peter Isotalo",
    "File:Velar nasal.ogg": "Peter Isotalo",
    "File:Alveolar lateral approximant.ogg": "Peter Isotalo",
    "File:Voiceless labiodental fricative.ogg": "Peter Isotalo",
    "File:Voiceless velar fricative.ogg": "Peter Isotalo",
    "File:Voiceless alveolar sibilant.ogg": "Peter Isotalo",
    "File:Voiceless alveolar sibilant affricate.oga": "Peter Isotalo",
    "File:Voiceless retroflex affricate.ogg": "Halibutt",
    "File:Voiceless retroflex sibilant.ogg": "Peter Isotalo",
    "File:Voiceless alveolo-palatal affricate.ogg": "Halibutt",
    "File:Voiceless alveolo-palatal sibilant.ogg": "Peter Isotalo",
    "File:Retroflex Approximant2.oga": "Peter Isotalo",
    "File:En-us-er.ogg": "Pigsonthewing",
    "File:PR-open front unrounded vowel.ogg": "Jbdowse",
    "File:Close-mid back rounded vowel.ogg": "Denelson83",
    "File:Close-mid back unrounded vowel.ogg": "Denelson83",
    "File:Close front unrounded vowel.ogg": "Denelson83",
    "File:Close back rounded vowel.ogg": "Denelson83",
    "File:Close front rounded vowel.ogg": "Denelson83",
}


# Local MP3 filename, Commons file title, attribution note.
# Keep this list limited to direct IPA samples that are not covered by the
# official IPA chart downloader. Do not add generated or composite audio here.
AUDIO_SOURCES = [
    ("mandarin_ipa_p_aspirated.mp3", "File:Aspirated voiceless bilabial stop.ogg", "Direct IPA [pʰ] sample, transcoded to MP3."),
    ("mandarin_ipa_ts.mp3", "File:Voiceless alveolar sibilant affricate.oga", "Direct IPA [ts] sample, transcoded to MP3."),
    ("mandarin_ipa_t_retroflex_affricate.mp3", "File:Voiceless retroflex affricate.ogg", "Direct IPA [t͡ʂ] sample; source also lists [ʈʂ]/[tʂ] variants, transcoded to MP3."),
    ("mandarin_ipa_t_alveolopalatal_affricate.mp3", "File:Voiceless alveolo-palatal affricate.ogg", "Direct IPA [t͡ɕ] sample; source also lists [tɕ]/[cɕ] variants, transcoded to MP3."),
]


def strip_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value or "")
    return html.unescape(value).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download direct Wikimedia IPA/phonetic sample audio and transcode it to MP3."
    )
    parser.add_argument("--delay", type=float, default=10.0, help="seconds to wait after each actual download")
    parser.add_argument("--skip-download", action="store_true", help="only clean media/ and rewrite the manifest from existing direct MP3 files")
    return parser.parse_args()


def require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("缺少 ffmpeg，无法转码 MP3。")


def open_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            wait_seconds = 60 * attempt
            print(f"HTTP 429 from Wikimedia; waiting {wait_seconds}s before retry", flush=True)
            time.sleep(wait_seconds)
    raise RuntimeError("unreachable retry state")


def commons_query(titles: list[str]) -> dict[str, Any]:
    params = {
        "action": "query",
        "titles": "|".join(titles),
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    return open_json(COMMONS_API + "?" + urllib.parse.urlencode(params))


def fetch_metadata(sources: list[tuple[str, str, str]]) -> dict[str, dict[str, Any]]:
    titles = sorted({source_title for _, source_title, _ in sources})
    pages_by_title: dict[str, dict[str, Any]] = {}
    for index in range(0, len(titles), 40):
        data = commons_query(titles[index : index + 40])
        for page in data.get("query", {}).get("pages", {}).values():
            if "missing" not in page:
                pages_by_title[page["title"]] = page
    missing = [title for title in titles if title not in pages_by_title]
    for title in missing:
        print(f"skipped metadata: {title} not found", flush=True)
    return pages_by_title


def source_metadata_row(filename: str, source_title: str, notes: str, page: dict[str, Any]) -> dict[str, str] | None:
    imageinfo = page["imageinfo"][0]
    metadata = imageinfo.get("extmetadata", {})
    author = AUTHOR_OVERRIDES.get(source_title, "")
    if not author:
        author = strip_html(metadata.get("Artist", {}).get("value", ""))
    if not author:
        author = strip_html(metadata.get("Credit", {}).get("value", ""))
    license_name = strip_html(
        metadata.get("LicenseShortName", {}).get("value", "")
        or metadata.get("UsageTerms", {}).get("value", "")
    )
    license_url = strip_html(metadata.get("LicenseUrl", {}).get("value", ""))
    if not author or not license_name or not license_url:
        print(f"skipped {filename}: missing author/license metadata", flush=True)
        return None
    return {
        "filename": filename,
        "source_project": "Wikimedia Commons",
        "source_title": source_title,
        "source_url": imageinfo["descriptionurl"],
        "author": author,
        "license": license_name,
        "license_url": license_url,
        "notes": notes,
    }


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def transcode_to_mp3(source: Path, target: Path) -> None:
    target.parent.mkdir(exist_ok=True)
    run_ffmpeg(["-i", str(source), "-vn", "-codec:a", "libmp3lame", "-q:a", "4", str(target)])


def download_source(url: str, target: Path) -> bool:
    if target.exists() and target.stat().st_size > 0:
        return False
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix or ".ogg"
    for attempt in range(1, 4):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix) as source_file:
                with urllib.request.urlopen(request, timeout=60) as response:
                    source_file.write(response.read())
                    source_file.flush()
                transcode_to_mp3(Path(source_file.name), target)
            return True
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            wait_seconds = 90 * attempt
            print(f"HTTP 429 while downloading; waiting {wait_seconds}s before retry", flush=True)
            time.sleep(wait_seconds)
    return True


def remove_stale_non_mp3() -> None:
    for path in MEDIA_DIR.iterdir():
        if path.is_file() and path.suffix.lower() in {".ogg", ".oga", ".wav", ".m4a", ".flac"}:
            path.unlink()


def cleanup_unmanifested_mp3(rows: dict[str, dict[str, str]]) -> None:
    valid = set(rows)
    for path in MEDIA_DIR.glob("*.mp3"):
        if path.name not in valid:
            path.unlink()


def write_manifest(rows: dict[str, dict[str, str]]) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MEDIA_MANIFEST_FIELDS)
        writer.writeheader()
        for filename in sorted(rows):
            writer.writerow(rows[filename])


def load_existing_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            row["filename"]: row
            for row in csv.DictReader(file)
            if row.get("filename")
        }


def existing_direct_rows() -> dict[str, dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return {}
    allowed = {filename for filename, _, _ in AUDIO_SOURCES}
    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        return {
            row["filename"]: row
            for row in csv.DictReader(file)
            if row.get("filename") in allowed and (MEDIA_DIR / row["filename"]).exists()
        }


def existing_rows_only(rows: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        filename: row
        for filename, row in rows.items()
        if (MEDIA_DIR / filename).exists()
    }


def main() -> None:
    args = parse_args()
    require_ffmpeg()
    MEDIA_DIR.mkdir(exist_ok=True)

    if args.skip_download:
        rows = existing_rows_only(load_existing_manifest())
    else:
        existing_manifest = load_existing_manifest()
        rows: dict[str, dict[str, str]] = dict(existing_manifest)
        pages_by_title = fetch_metadata(AUDIO_SOURCES)
        for filename, source_title, notes in AUDIO_SOURCES:
            page = pages_by_title.get(source_title)
            if not page:
                continue
            row = source_metadata_row(filename, source_title, notes, page)
            if row is None:
                continue
            target = MEDIA_DIR / filename
            previous = existing_manifest.get(filename, {})
            if target.exists() and (
                previous.get("source_project") != "Wikimedia Commons"
                or previous.get("source_title") != source_title
            ):
                target.unlink()
            did_download = download_source(page["imageinfo"][0]["url"], target)
            action = "downloaded" if did_download else "kept existing"
            print(f"{action} {filename} <- {source_title}", flush=True)
            if did_download:
                time.sleep(args.delay)
            rows[filename] = row

    remove_stale_non_mp3()
    rows = existing_rows_only(rows)
    write_manifest(rows)
    direct_count = sum(1 for filename, _, _ in AUDIO_SOURCES if filename in rows)
    print(f"wrote {MANIFEST_PATH}", flush=True)
    print(f"direct Wikimedia audio files: {direct_count}", flush=True)


if __name__ == "__main__":
    main()
