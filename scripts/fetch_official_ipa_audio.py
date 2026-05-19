#!/usr/bin/env python3
"""Fetch matching audio from the IPA official interactive chart.

The interactive chart serves MP3 files directly from predictable paths. This
script imports only non-composite IPA samples that map cleanly to this deck.
It does not synthesize, concatenate, or infer missing Mandarin-specific sounds.
"""

from __future__ import annotations

import argparse
import csv
import time
import urllib.error
import urllib.request
from pathlib import Path

import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from build_deck import MEDIA_DIR, MEDIA_MANIFEST_FIELDS, MEDIA_MANIFEST_PATH  # noqa: E402


BASE_URL = "https://www.internationalphoneticassociation.org/IPAcharts/common_files/sounds"
SOURCE_URL = "https://www.internationalphoneticassociation.org/IPAcharts/IPA_charts_EI/IPA_charts_EI.html"
USER_AGENT = "Chinese-IPA-Anki/0.4 official IPA audio fetcher"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"

AUTHORS = {
    "JE": "J. Esling",
    "JH": "J. House",
    "PL": "P. Ladefoged",
    "JW": "J. Wells",
}


# target filename, IPA display, official chart MP3 basename, note.
OFFICIAL_AUDIO = [
    ("mandarin_ipa_p.mp3", "[p]", "0070", "voiceless bilabial plosive"),
    ("mandarin_ipa_t.mp3", "[t]", "0074", "voiceless dental/alveolar plosive"),
    ("mandarin_ipa_t_aspirated.mp3", "[tʰ]", "02B0_1", "aspirated diacritic example tʰ"),
    ("mandarin_ipa_k.mp3", "[k]", "006B", "voiceless velar plosive"),
    ("mandarin_ipa_m.mp3", "[m]", "006D", "voiced bilabial nasal"),
    ("mandarin_ipa_n.mp3", "[n]", "006E", "voiced dental/alveolar nasal"),
    ("mandarin_ipa_eng.mp3", "[ŋ]", "014B", "voiced velar nasal"),
    ("mandarin_ipa_l.mp3", "[l]", "006C", "voiced dental/alveolar lateral approximant"),
    ("mandarin_ipa_f.mp3", "[f]", "0066", "voiceless labiodental fricative"),
    ("mandarin_ipa_x.mp3", "[x]", "0078", "voiceless velar fricative"),
    ("mandarin_ipa_s.mp3", "[s]", "0073", "voiceless alveolar fricative"),
    ("mandarin_ipa_retroflex_sibilant.mp3", "[ʂ]", "0282", "voiceless retroflex fricative"),
    ("mandarin_ipa_alveolopalatal_sibilant.mp3", "[ɕ]", "0255", "voiceless alveolo-palatal fricative"),
    ("mandarin_ipa_retroflex_approximant.mp3", "[ɻ]", "027B", "voiced retroflex approximant"),
    ("mandarin_ipa_a.mp3", "[a]", "0061", "open front unrounded vowel"),
    ("mandarin_ipa_o.mp3", "[o]", "006F", "close-mid back rounded vowel"),
    ("mandarin_ipa_gamma.mp3", "[ɤ]", "0264", "close-mid back unrounded vowel"),
    ("mandarin_ipa_i.mp3", "[i]", "0069", "close front unrounded vowel"),
    ("mandarin_ipa_u.mp3", "[u]", "0075", "close back rounded vowel"),
    ("mandarin_ipa_y.mp3", "[y]", "0079", "close front rounded vowel"),
    ("mandarin_ipa_er.mp3", "[ɚ]", "02DE_1", "rhoticity example ɚ"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch selected official IPA chart MP3 audio.")
    parser.add_argument("--author", choices=sorted(AUTHORS), default="JE", help="recording set to use")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to wait after each download")
    parser.add_argument("--overwrite", action="store_true", help="replace existing files")
    return parser.parse_args()


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


def source_row(filename: str, ipa: str, basename: str, note: str, author_key: str) -> dict[str, str]:
    author = AUTHORS[author_key]
    return {
        "filename": filename,
        "source_project": "International Phonetic Association",
        "source_title": f"Interactive IPA Chart {ipa} audio ({author_key}/{basename}.mp3)",
        "source_url": SOURCE_URL,
        "author": author,
        "license": "CC BY-SA 4.0",
        "license_url": LICENSE_URL,
        "notes": f"Official IPA interactive chart audio by {author}; {note}.",
    }


def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())


def main() -> None:
    args = parse_args()
    MEDIA_DIR.mkdir(exist_ok=True)
    manifest = load_manifest()
    imported: list[str] = []
    skipped: list[str] = []

    for filename, ipa, basename, note in OFFICIAL_AUDIO:
        target = MEDIA_DIR / filename
        if target.exists() and not args.overwrite:
            skipped.append(filename)
            continue
        url = f"{BASE_URL}/{args.author}/{basename}.mp3"
        try:
            download(url, target)
        except urllib.error.HTTPError as error:
            print(f"skipped {ipa}: HTTP {error.code} for {url}", flush=True)
            continue
        manifest[filename] = source_row(filename, ipa, basename, note, args.author)
        write_manifest(manifest)
        imported.append(f"{ipa} -> {filename}")
        if args.delay > 0:
            time.sleep(args.delay)

    write_manifest(manifest)
    print(f"imported {len(imported)} official IPA audio file(s)")
    for line in imported:
        print(line)
    if skipped:
        print(f"skipped existing {len(skipped)} file(s); pass --overwrite to replace")


if __name__ == "__main__":
    main()
