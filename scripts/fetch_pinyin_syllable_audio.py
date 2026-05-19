#!/usr/bin/env python3
"""Fetch Mandarin pinyin syllable demo audio for IPA cards.

These files are not pure IPA-symbol audio. They are natural Mandarin syllable
recordings used as consistent demonstrations for this Mandarin IPA deck. The
generated manifest rows label them accordingly.
"""

from __future__ import annotations

import argparse
import csv
import time
import urllib.request
from pathlib import Path

import sys

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from build_deck import MEDIA_DIR, MEDIA_MANIFEST_FIELDS, MEDIA_MANIFEST_PATH  # noqa: E402


BASE_URL = "https://raw.githubusercontent.com/davinfifield/mp3-chinese-pinyin-sound/master/mp3"
SOURCE_URL = "https://github.com/davinfifield/mp3-chinese-pinyin-sound"
LICENSE_URL = "https://github.com/davinfifield/mp3-chinese-pinyin-sound/blob/master/LICENSE"
USER_AGENT = "Chinese-IPA-Anki/0.6 pinyin syllable demo fetcher"


# target filename, pinyin audio basename, IPA/card target, note.
PINYIN_DEMOS = [
    ("mandarin_ipa_p.mp3", "ba1", "[p]", "b / ba1 demonstrates unaspirated bilabial initial in a Mandarin syllable."),
    ("mandarin_ipa_p_aspirated.mp3", "pa1", "[pʰ]", "p / pa1 demonstrates aspirated bilabial initial in a Mandarin syllable."),
    ("mandarin_ipa_m.mp3", "ma1", "[m]", "m / ma1 demonstrates bilabial nasal initial in a Mandarin syllable."),
    ("mandarin_ipa_f.mp3", "fa1", "[f]", "f / fa1 demonstrates labiodental fricative initial in a Mandarin syllable."),
    ("mandarin_ipa_t.mp3", "da1", "[t]", "d / da1 demonstrates unaspirated alveolar initial in a Mandarin syllable."),
    ("mandarin_ipa_t_aspirated.mp3", "ta1", "[tʰ]", "t / ta1 demonstrates aspirated alveolar initial in a Mandarin syllable."),
    ("mandarin_ipa_n.mp3", "na1", "[n]", "n / na1 demonstrates alveolar nasal initial in a Mandarin syllable."),
    ("mandarin_ipa_l.mp3", "la1", "[l]", "l / la1 demonstrates alveolar lateral initial in a Mandarin syllable."),
    ("mandarin_ipa_k.mp3", "ga1", "[k]", "g / ga1 demonstrates unaspirated velar initial in a Mandarin syllable."),
    ("mandarin_ipa_k_aspirated.mp3", "ka1", "[kʰ]", "k / ka1 demonstrates aspirated velar initial in a Mandarin syllable."),
    ("mandarin_ipa_x.mp3", "ha1", "[x]", "h / ha1 demonstrates Mandarin h in a Mandarin syllable."),
    ("mandarin_ipa_t_alveolopalatal_affricate.mp3", "ji1", "[t͡ɕ]", "j / ji1 demonstrates unaspirated alveolo-palatal affricate in a Mandarin syllable."),
    ("mandarin_ipa_t_alveolopalatal_affricate_aspirated.mp3", "qi1", "[t͡ɕʰ]", "q / qi1 demonstrates aspirated alveolo-palatal initial."),
    ("mandarin_ipa_alveolopalatal_sibilant.mp3", "xi1", "[ɕ]", "x / xi1 demonstrates alveolo-palatal fricative in a Mandarin syllable."),
    ("mandarin_ipa_t_retroflex_affricate.mp3", "zha1", "[t͡ʂ]", "zh / zha1 demonstrates unaspirated retroflex affricate in a Mandarin syllable."),
    ("mandarin_ipa_t_retroflex_affricate_aspirated.mp3", "cha1", "[t͡ʂʰ]", "ch / cha1 demonstrates aspirated retroflex affricate."),
    ("mandarin_ipa_retroflex_sibilant.mp3", "sha1", "[ʂ]", "sh / sha1 demonstrates retroflex fricative in a Mandarin syllable."),
    ("mandarin_ipa_retroflex_approximant.mp3", "ri1", "[ɻ]", "r / ri1 demonstrates the Mandarin retroflex r-like initial in a Mandarin syllable."),
    ("mandarin_ipa_ts.mp3", "za1", "[ts]", "z / za1 demonstrates unaspirated alveolar affricate in a Mandarin syllable."),
    ("mandarin_ipa_ts_aspirated.mp3", "ca1", "[tsʰ]", "c / ca1 demonstrates aspirated alveolar affricate."),
    ("mandarin_ipa_s.mp3", "sa1", "[s]", "s / sa1 demonstrates alveolar fricative in a Mandarin syllable."),
    ("mandarin_ipa_zero.mp3", "a1", "∅", "a1 demonstrates a Mandarin syllable without an initial consonant."),
    ("mandarin_ipa_a.mp3", "a1", "[a]", "a1 demonstrates the Mandarin final a."),
    ("mandarin_ipa_o.mp3", "bo1", "[o]", "bo1 demonstrates the Mandarin final o with a carrier initial."),
    ("mandarin_ipa_gamma.mp3", "e1", "[ɤ]", "e1 demonstrates the Mandarin final e."),
    ("mandarin_ipa_i.mp3", "yi1", "[i]", "yi1 demonstrates the Mandarin final i in zero-initial spelling."),
    ("mandarin_ipa_u.mp3", "wu1", "[u]", "wu1 demonstrates the Mandarin final u in zero-initial spelling."),
    ("mandarin_ipa_y.mp3", "yu1", "[y]", "yu1 demonstrates the Mandarin final ü in zero-initial spelling."),
    ("mandarin_ipa_ai.mp3", "ai1", "[ai]", "ai1 demonstrates the Mandarin final ai."),
    ("mandarin_ipa_ei.mp3", "ei1", "[ei]", "ei1 demonstrates the Mandarin final ei."),
    ("mandarin_ipa_au.mp3", "ao1", "[au]", "ao1 demonstrates the Mandarin final ao."),
    ("mandarin_ipa_ou.mp3", "ou1", "[ou]", "ou1 demonstrates the Mandarin final ou."),
    ("mandarin_ipa_an.mp3", "an1", "[an]", "an1 demonstrates the Mandarin final an."),
    ("mandarin_ipa_schwa_n.mp3", "en1", "[ən]", "en1 demonstrates the Mandarin final en."),
    ("mandarin_ipa_alpha_eng.mp3", "ang1", "[ɑŋ]", "ang1 demonstrates the Mandarin final ang."),
    ("mandarin_ipa_eng.mp3", "ang1", "[ŋ]", "ang1 demonstrates the Mandarin velar nasal coda."),
    ("mandarin_ipa_schwa_eng.mp3", "deng1", "[əŋ]", "deng1 demonstrates the Mandarin final eng with a carrier initial."),
    ("mandarin_ipa_upsilon_eng.mp3", "gong1", "[ʊŋ]", "gong1 demonstrates the Mandarin final ong with a carrier initial."),
    ("mandarin_ipa_ja.mp3", "ya1", "[ja]", "ya1 demonstrates the Mandarin final ia in zero-initial spelling."),
    ("mandarin_ipa_j_epsilon.mp3", "ye1", "[jɛ]", "ye1 demonstrates the Mandarin final ie in zero-initial spelling."),
    ("mandarin_ipa_jau.mp3", "yao1", "[jau]", "yao1 demonstrates the Mandarin final iao in zero-initial spelling."),
    ("mandarin_ipa_jou.mp3", "you1", "[jou]", "you1 demonstrates the Mandarin final iu/iou in zero-initial spelling."),
    ("mandarin_ipa_j_epsilon_n.mp3", "yan1", "[jɛn]", "yan1 demonstrates the Mandarin final ian in zero-initial spelling."),
    ("mandarin_ipa_in.mp3", "yin1", "[in]", "yin1 demonstrates the Mandarin final in in zero-initial spelling."),
    ("mandarin_ipa_j_alpha_eng.mp3", "yang1", "[jɑŋ]", "yang1 demonstrates the Mandarin final iang in zero-initial spelling."),
    ("mandarin_ipa_i_eng.mp3", "ying1", "[iŋ]", "ying1 demonstrates the Mandarin final ing in zero-initial spelling."),
    ("mandarin_ipa_j_upsilon_eng.mp3", "yong1", "[jʊŋ]", "yong1 demonstrates the Mandarin final iong in zero-initial spelling."),
    ("mandarin_ipa_wa.mp3", "wa1", "[wa]", "wa1 demonstrates the Mandarin final ua in zero-initial spelling."),
    ("mandarin_ipa_wo.mp3", "wo1", "[wo]", "wo1 demonstrates the Mandarin final uo in zero-initial spelling."),
    ("mandarin_ipa_wai.mp3", "wai1", "[wai]", "wai1 demonstrates the Mandarin final uai in zero-initial spelling."),
    ("mandarin_ipa_wei.mp3", "wei1", "[wei]", "wei1 demonstrates the Mandarin final ui/uei in zero-initial spelling."),
    ("mandarin_ipa_wan.mp3", "wan1", "[wan]", "wan1 demonstrates the Mandarin final uan in zero-initial spelling."),
    ("mandarin_ipa_w_schwa_n.mp3", "wen1", "[wən]", "wen1 demonstrates the Mandarin final un/uen in zero-initial spelling."),
    ("mandarin_ipa_w_alpha_eng.mp3", "wang1", "[wɑŋ]", "wang1 demonstrates the Mandarin final uang in zero-initial spelling."),
    ("mandarin_ipa_w_schwa_eng.mp3", "weng1", "[wəŋ]", "weng1 demonstrates the Mandarin final ueng in zero-initial spelling."),
    ("mandarin_ipa_y_epsilon.mp3", "yue1", "[yɛ]", "yue1 demonstrates the Mandarin final üe in zero-initial spelling."),
    ("mandarin_ipa_y_epsilon_n.mp3", "yuan1", "[yɛn]", "yuan1 demonstrates the Mandarin final üan in zero-initial spelling."),
    ("mandarin_ipa_y_n.mp3", "yun1", "[yn]", "yun1 demonstrates the Mandarin final ün in zero-initial spelling."),
    ("mandarin_ipa_er.mp3", "er2", "[ɚ]", "er2 demonstrates the Mandarin er final as a full syllable."),
    ("mandarin_ipa_apical_alveolar_vowel.mp3", "zi1", "[ɿ]", "zi1 demonstrates the apical vowel after z/c/s."),
    ("mandarin_ipa_apical_retroflex_vowel.mp3", "zhi1", "[ʅ]", "zhi1 demonstrates the apical vowel after zh/ch/sh/r."),
    ("mandarin_ipa_tone_1.mp3", "ma1", "[˥]", "ma1 demonstrates Mandarin first tone."),
    ("mandarin_ipa_tone_2.mp3", "ma2", "[˧˥]", "ma2 demonstrates Mandarin second tone."),
    ("mandarin_ipa_tone_3.mp3", "ma3", "[˨˩˦]", "ma3 demonstrates Mandarin third tone."),
    ("mandarin_ipa_tone_4.mp3", "ma4", "[˥˩]", "ma4 demonstrates Mandarin fourth tone."),
    ("mandarin_ipa_tone_5.mp3", "ma5", "◌̆", "ma5 demonstrates Mandarin neutral tone."),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch pinyin syllable demo MP3 audio.")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds to wait after each download")
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


def source_row(filename: str, syllable: str, ipa: str, note: str) -> dict[str, str]:
    return {
        "filename": filename,
        "source_project": "Pinyin syllable demo",
        "source_title": f"mp3-chinese-pinyin-sound {syllable}.mp3 for {ipa}",
        "source_url": f"{BASE_URL}/{syllable}.mp3",
        "author": "davinfifield/mp3-chinese-pinyin-sound contributors",
        "license": "Unlicense",
        "license_url": LICENSE_URL,
        "notes": f"{note} This is a full Mandarin syllable demo, not isolated IPA-symbol audio.",
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

    for filename, syllable, ipa, note in PINYIN_DEMOS:
        target = MEDIA_DIR / filename
        if target.exists() and not args.overwrite:
            skipped.append(filename)
            continue
        url = f"{BASE_URL}/{syllable}.mp3"
        download(url, target)
        manifest[filename] = source_row(filename, syllable, ipa, note)
        imported.append(f"{ipa} <- {syllable} -> {filename}")
        if args.delay > 0:
            time.sleep(args.delay)

    write_manifest(manifest)
    print(f"imported {len(imported)} pinyin syllable demo file(s)")
    for line in imported:
        print(line)
    if skipped:
        print(f"skipped existing {len(skipped)} file(s); pass --overwrite to replace")


if __name__ == "__main__":
    main()
