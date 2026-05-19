#!/usr/bin/env python3
"""Import IPA-chart audio first, then pinyin syllable fallback audio.

Wikipedia/Commons downloads are intentionally single-threaded and slow. The
default delay is 25 seconds before each Wikimedia request. Fallback audio is
read from the local zispace/hanyu-pinyin-audio v0.1 zip files already saved
under _sources/.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from build_deck import MEDIA_DIR, MEDIA_MANIFEST_FIELDS, MEDIA_MANIFEST_PATH  # noqa: E402


WIKI_SOURCE_DIR = PROJECT_DIR / "_sources" / "wikipedia-ipa-charts"
ZISPACE_SOURCE_DIR = PROJECT_DIR / "_sources" / "zispace-hanyu-pinyin-audio-v0.1"
WIKI_PAGE_URLS = {
    "consonant": "https://en.wikipedia.org/wiki/IPA_consonant_chart_with_audio",
    "vowel": "https://en.wikipedia.org/wiki/IPA_vowel_chart_with_audio",
}
ZISPACE_RELEASE_URL = "https://github.com/zispace/hanyu-pinyin-audio/releases/tag/v0.1"
USER_AGENT = "MandarinIPAAnki/0.2 personal educational IPA audio importer"


@dataclass(frozen=True)
class Fallback:
    zip_name: str
    stem: str
    note: str = ""


@dataclass(frozen=True)
class Target:
    filename: str
    ipa: str
    wiki_aliases: tuple[str, ...] = ()
    fallback: tuple[Fallback, ...] = ()
    note: str = ""


def z(stem: str, ipa: str, aliases: Iterable[str] = (), fallback: Iterable[Fallback] = (), note: str = "") -> Target:
    return Target(
        filename=f"mandarin_{stem}.mp3",
        ipa=ipa,
        wiki_aliases=tuple(aliases),
        fallback=tuple(fallback),
        note=note,
    )


def hug(stem: str, note: str = "") -> Fallback:
    return Fallback("github-hugolpz-audio.zip", stem, note)


def hug_more(stem: str, note: str = "") -> Fallback:
    return Fallback("github-hugolpz-more.zip", stem, note)


TARGETS: list[Target] = [
    z("ipa_p", "[p]", ["p"], [hug("ba1")]),
    z("ipa_p_aspirated", "[pʰ]", [], [hug("pa1", "aspirated Mandarin p in pa1")]),
    z("ipa_t", "[t]", ["t"], [hug("da1")]),
    z("ipa_t_aspirated", "[tʰ]", [], [hug("ta1", "aspirated Mandarin t in ta1")]),
    z("ipa_k", "[k]", ["k"], [hug("ga1")]),
    z("ipa_k_aspirated", "[kʰ]", [], [hug("ka1", "aspirated Mandarin k in ka1")]),
    z("ipa_m", "[m]", ["m"], [hug("ma1")]),
    z("ipa_m_voiceless", "[m̥]", ["m̥"], [hug_more("m1")]),
    z("ipa_syllabic_m", "[m̩]", [], [hug_more("m1", "syllabic m-like Mandarin interjection")]),
    z("ipa_n", "[n]", ["n"], [hug("na1")]),
    z("ipa_n_palatalized", "[nʲ]", [], [hug("ni1", "Mandarin n before high front vowel")]),
    z("ipa_syllabic_n", "[n̩]", [], [hug_more("n1", "syllabic n-like Mandarin interjection")]),
    z("ipa_eng", "[ŋ]", ["ŋ"], [hug("ang1")]),
    z("ipa_eng_voiceless", "[ŋ̊]", ["ŋ̊"], [hug_more("ng1")]),
    z("ipa_syllabic_eng", "[ŋ̍]", [], [hug_more("ng1", "syllabic ng-like Mandarin interjection")]),
    z("ipa_l", "[l]", ["l"], [hug("la1")]),
    z("ipa_f", "[f]", ["f"], [hug("fa1")]),
    z("ipa_x", "[x]", ["x"], [hug("ha1")]),
    z("ipa_h", "[h]", ["h"], [hug("ha1")]),
    z("ipa_alveolopalatal_sibilant", "[ɕ]", ["ɕ"], [hug("xi1")]),
    z("ipa_t_alveolopalatal_affricate", "[t͡ɕ]", ["t͡ɕ", "tɕ"], [hug("ji1")]),
    z("ipa_t_alveolopalatal_affricate_aspirated", "[t͡ɕʰ]", [], [hug("qi1", "aspirated Mandarin q in qi1")]),
    z("ipa_ts", "[t͡s]", ["t͡s", "ts"], [hug("zi1")]),
    z("ipa_ts_aspirated", "[t͡sʰ]", [], [hug("ci1", "aspirated Mandarin c in ci1")]),
    z("ipa_t_retroflex_affricate", "[ʈ͡ʂ]", ["ʈ͡ʂ", "t͡ʂ", "tʂ"], [hug("zhi1")]),
    z("ipa_t_retroflex_affricate_aspirated", "[ʈ͡ʂʰ]", [], [hug("chi1", "aspirated Mandarin ch in chi1")]),
    z("ipa_retroflex_sibilant", "[ʂ]", ["ʂ"], [hug("shi1")]),
    z("ipa_retroflex_sibilant_voiced", "[ʐ]", ["ʐ"], [hug("ri4")]),
    z("ipa_s", "[s]", ["s"], [hug("si1")]),
    z("ipa_z", "[z]", ["z"], [hug("zi1")]),
    z("ipa_glottal_stop", "[ʔ]", ["ʔ"], [hug("a1")]),
    z("ipa_j", "[j]", ["j"], [hug("yi1")]),
    z("ipa_j_stroked", "[ɉ]", [], [hug("ji1", "nearest Mandarin j-like syllable demo")]),
    z("ipa_w", "[w]", ["w"], [hug("wu1")]),
    z("ipa_labiopalatal_approximant", "[ɥ]", ["ɥ"], [hug("yu1")]),
    z("ipa_retroflex_approximant", "[ɻ]", ["ɻ"], [hug("ri4")]),
    z("ipa_syllabic_alveolar_approximant", "[ɹ̩]", [], [hug("ri4", "nearest Mandarin r/ri syllable demo")]),
    z("ipa_syllabic_retroflex_approximant", "[ɻ̩]", [], [hug("ri4", "nearest Mandarin r/ri syllable demo")]),
    z("ipa_a", "[a]", ["a"], [hug("a1")]),
    z("ipa_a_central", "[ä]", ["ä"], [hug("a1")]),
    z("ipa_alpha", "[ɑ]", ["ɑ"], [hug("ang1")]),
    z("ipa_e_lowered", "[e̞]", ["e̞"], [hug("ye1")]),
    z("ipa_schwa", "[ə]", ["ə"], [hug("en1")]),
    z("ipa_er", "[ɚ]", [], [hug("er2")]),
    z("ipa_er_nasalized", "[ɚ̃]", [], [hug("er2", "nearest er syllable demo; not nasalized")]),
    z("ipa_epsilon", "[ɛ]", ["ɛ"], [hug("ye1")]),
    z("ipa_i", "[i]", ["i"], [hug("yi1")]),
    z("ipa_o_lowered", "[o̞]", ["o̞"], [hug("wo1")]),
    z("ipa_o_lowered_rhotic", "[o̞˞]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_oe_less_rounded", "[œ̜]", ["œ̜", "œ"], [hug("yue1")]),
    z("ipa_u", "[u]", ["u"], [hug("wu1")]),
    z("ipa_u_rhotic", "[u˞]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_upsilon", "[ʊ]", ["ʊ"], [hug("gong1")]),
    z("ipa_upsilon_nasalized_rhotic", "[ʊ̃˞]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_gamma", "[ɤ]", ["ɤ"], [hug("e1")]),
    z("ipa_gamma_lowered", "[ɤ̞]", ["ɤ̞"], [hug("e1")]),
    z("ipa_gamma_rhotic", "[ɤ˞]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_y", "[y]", ["y"], [hug("yu1")]),
    z("ipa_ai", "[ai̯]", [], [hug("ai1")]),
    z("ipa_a_central_er", "[äɚ̯]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_a_central_nasal_er", "[ä̃ɚ̯̃]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_turned_a_er", "[ɐɚ̯]", [], [hug("er2", "nearest rhotic syllable demo")]),
    z("ipa_alpha_u", "[ɑu̯]", [], [hug("ao1")]),
    z("ipa_alpha_u_rhotic", "[ɑu̯˞]", [], [hug("ao1", "base ao syllable demo; not erhua")]),
    z("ipa_ei", "[ei̯]", [], [hug("ei1")]),
    z("ipa_ou", "[ou̯]", [], [hug("ou1")]),
    z("ipa_ou_rhotic", "[ou̯˞]", [], [hug("ou1", "base ou syllable demo; not erhua")]),
    z("ipa_apical_alveolar_vowel", "[ɿ]", [], [hug("zi1")]),
    z("ipa_apical_retroflex_vowel", "[ʅ]", [], [hug("zhi1")]),
    z("ipa_tone_1", "˥˥", [], [hug("ma1")]),
    z("ipa_tone_2", "˧˥", [], [hug("ma2")]),
    z("ipa_tone_3", "˨˩˦", [], [hug("ma3")]),
    z("ipa_tone_4", "˥˩", [], [hug("ma4")]),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Wikipedia IPA chart audio with zispace fallback.")
    parser.add_argument("--delay", type=float, default=25.0, help="seconds before each Wikimedia download")
    parser.add_argument("--overwrite", action="store_true", help="replace existing media files")
    parser.add_argument("--clear-media", action="store_true", help="remove existing audio files and reset manifest first")
    parser.add_argument("--dry-run", action="store_true", help="show the plan without writing files")
    return parser.parse_args()


def strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value)


def commons_file_url(file_title: str) -> str:
    return "https://commons.wikimedia.org/wiki/File:" + file_title.replace(" ", "_")


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
    MEDIA_DIR.mkdir(exist_ok=True)
    with MEDIA_MANIFEST_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MEDIA_MANIFEST_FIELDS)
        writer.writeheader()
        for filename in sorted(rows):
            writer.writerow(rows[filename])


def parse_wiki_audio_index() -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for page_key, page_url in WIKI_PAGE_URLS.items():
        path = WIKI_SOURCE_DIR / f"{page_key}.html"
        if not path.exists():
            raise FileNotFoundError(f"缺少 Wikipedia HTML：{path}")
        text = path.read_text(encoding="utf-8", errors="replace")
        for chunk in text.split('<div class="IPA-audiocell"')[1:]:
            chunk = '<div class="IPA-audiocell"' + chunk
            symbol_match = re.search(
                r'<div class="IPA-audiocell-symbol">.*?<span class="IPA"[^>]*>(.*?)</span>',
                chunk,
                flags=re.S,
            )
            data_match = re.search(r'data-ooui="(.*?)"', chunk, flags=re.S)
            file_match = re.search(r'<a href="/wiki/File:[^"]+" title="File:([^"]+)"', chunk)
            if not (symbol_match and data_match and file_match):
                continue
            symbol = html.unescape(strip_tags(symbol_match.group(1))).strip()
            data = json.loads(html.unescape(data_match.group(1)))
            href = data.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            file_title = html.unescape(file_match.group(1)).strip()
            row = {
                "symbol": symbol,
                "page_url": page_url,
                "file_title": file_title,
                "source_url": commons_file_url(file_title),
                "download_url": href,
            }
            index.setdefault(symbol, []).append(row)
    return index


def find_wiki_candidate(target: Target, index: dict[str, list[dict[str, str]]]) -> dict[str, str] | None:
    for alias in target.wiki_aliases:
        candidates = index.get(alias)
        if candidates:
            return candidates[0]
    return None


def find_fallback_file(fallback: Fallback) -> tuple[bytes, str] | None:
    zip_path = ZISPACE_SOURCE_DIR / fallback.zip_name
    if not zip_path.exists():
        return None
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            path = Path(info.filename)
            if path.stem.lower() == fallback.stem.lower() and path.suffix.lower() == ".mp3":
                return archive.read(info.filename), path.name
    return None


def download_wiki(candidate: dict[str, str], target: Path, delay: float) -> None:
    print(f"  sleep {delay:.0f}s before Wikimedia download", flush=True)
    time.sleep(delay)
    request = urllib.request.Request(candidate["download_url"], headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        target.write_bytes(response.read())


def wiki_manifest_row(target: Target, candidate: dict[str, str]) -> dict[str, str]:
    return {
        "filename": target.filename,
        "source_project": "Wikimedia Commons IPA chart audio",
        "source_title": f"File:{candidate['file_title']} for {target.ipa}",
        "source_url": candidate["source_url"],
        "author": "Wikimedia Commons contributors; see source file page",
        "license": "See source file page",
        "license_url": candidate["source_url"],
        "notes": f"Direct IPA chart audio from {candidate['page_url']}. {target.note}".strip(),
    }


def fallback_manifest_row(target: Target, fallback: Fallback, source_name: str) -> dict[str, str]:
    return {
        "filename": target.filename,
        "source_project": "Pinyin syllable demo",
        "source_title": f"zispace/hanyu-pinyin-audio pinyin syllable {source_name} for {target.ipa}",
        "source_url": ZISPACE_RELEASE_URL,
        "author": "zispace/hanyu-pinyin-audio source archive contributors",
        "license": "See upstream source archive; personal-use fallback",
        "license_url": ZISPACE_RELEASE_URL,
        "notes": (
            f"Fallback from {fallback.zip_name}. This is a full Mandarin syllable demo, "
            f"not isolated IPA-symbol audio. {fallback.note or target.note}"
        ).strip(),
    }


def clear_media() -> None:
    MEDIA_DIR.mkdir(exist_ok=True)
    for path in MEDIA_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".mp3", ".wav", ".ogg", ".oga", ".m4a", ".opus"}:
            path.unlink()
    write_manifest({})


def main() -> None:
    args = parse_args()
    MEDIA_DIR.mkdir(exist_ok=True)
    if args.clear_media and not args.dry_run:
        clear_media()

    index = parse_wiki_audio_index()
    manifest = load_manifest()
    imported_wiki = 0
    imported_fallback = 0
    skipped = 0
    missing: list[str] = []

    for target in TARGETS:
        out = MEDIA_DIR / target.filename
        candidate = find_wiki_candidate(target, index)
        source = "wiki" if candidate else "fallback"
        print(f"{target.filename}: {target.ipa} <- {source}", flush=True)

        if args.dry_run:
            if candidate:
                print(f"  wiki {candidate['symbol']} {candidate['file_title']}", flush=True)
            elif target.fallback:
                print(f"  fallback {target.fallback[0].zip_name}:{target.fallback[0].stem}.mp3", flush=True)
            else:
                missing.append(target.filename)
            continue

        if candidate:
            if out.exists() and not args.overwrite:
                skipped += 1
            else:
                download_wiki(candidate, out, args.delay)
                imported_wiki += 1
            manifest[target.filename] = wiki_manifest_row(target, candidate)
            write_manifest(manifest)
            continue

        wrote_fallback = False
        for fallback in target.fallback:
            found = find_fallback_file(fallback)
            if not found:
                continue
            data, source_name = found
            if not out.exists() or args.overwrite:
                out.write_bytes(data)
                imported_fallback += 1
            else:
                skipped += 1
            manifest[target.filename] = fallback_manifest_row(target, fallback, source_name)
            write_manifest(manifest)
            wrote_fallback = True
            break
        if not wrote_fallback:
            missing.append(target.filename)

    if not args.dry_run:
        write_manifest(manifest)

    print("\nsummary")
    print(f"wiki imported: {imported_wiki}")
    print(f"fallback imported: {imported_fallback}")
    print(f"skipped existing: {skipped}")
    print(f"missing: {len(missing)}")
    for name in missing:
        print(f"  missing {name}")


if __name__ == "__main__":
    main()
