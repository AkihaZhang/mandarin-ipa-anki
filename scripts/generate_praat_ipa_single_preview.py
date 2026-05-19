#!/usr/bin/env python3
"""Generate a Praat-based IPA single-sound preview pack.

This is a listening preview only. It writes generated MP3 files under output/
and does not modify the Anki deck, media/, or audio_manifest.csv.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "output" / "praat_ipa_single_preview"
WAV_DIR = OUTPUT_DIR / "wav"
MP3_DIR = OUTPUT_DIR / "mp3"
ZIP_PATH = OUTPUT_DIR / "Praat_IPA_Single_Sounds_Preview.zip"
MANIFEST_PATH = OUTPUT_DIR / "manifest.csv"
README_PATH = OUTPUT_DIR / "README.txt"

PRAAT = Path("/Applications/Praat.app/Contents/MacOS/Praat")
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
SAMPLE_RATE = 44100


@dataclass(frozen=True)
class Segment:
    index: int
    ipa: str
    label: str
    description: str
    kind: str
    params: tuple[float, ...] | tuple[int, int] = ()
    pinyin: str = ""

    @property
    def filename_stem(self) -> str:
        ipa_part = self.ipa.replace("/", "_")
        label = self.label.replace(" ", "_")
        return f"{self.index:03d}_{ipa_part}_{label}"


SEGMENTS = [
    Segment(1, "[p]", "b_unaspirated_bilabial_stop", "不送气双唇塞音；普通话 b。", "stop", (500, 2500), "b"),
    Segment(2, "[pʰ]", "p_aspirated_bilabial_stop", "送气双唇塞音；普通话 p。", "aspirated_stop", (500, 2500), "p"),
    Segment(3, "[m]", "m_bilabial_nasal", "双唇鼻音；普通话 m。", "sonorant", (250, 1000, 2200, 3300), "m"),
    Segment(4, "[f]", "f_labiodental_fricative", "唇齿擦音；普通话 f。", "fricative", (1200, 9000), "f"),
    Segment(5, "[t]", "d_unaspirated_alveolar_stop", "不送气齿龈塞音；普通话 d。", "stop", (2500, 6500), "d"),
    Segment(6, "[tʰ]", "t_aspirated_alveolar_stop", "送气齿龈塞音；普通话 t。", "aspirated_stop", (2500, 6500), "t"),
    Segment(7, "[n]", "n_alveolar_nasal", "齿龈鼻音；普通话 n。", "sonorant", (300, 1700, 2600, 3600), "n"),
    Segment(8, "[l]", "l_alveolar_lateral", "齿龈边音；普通话 l。", "sonorant", (350, 1300, 2600, 3600), "l"),
    Segment(9, "[k]", "g_unaspirated_velar_stop", "不送气软腭塞音；普通话 g。", "stop", (1200, 4200), "g"),
    Segment(10, "[kʰ]", "k_aspirated_velar_stop", "送气软腭塞音；普通话 k。", "aspirated_stop", (1200, 4200), "k"),
    Segment(11, "[x]", "h_velar_fricative", "软腭擦音；普通话 h 的宽式近似。", "fricative", (800, 3800), "h"),
    Segment(12, "[t͡ɕ]", "j_unaspirated_alveolopalatal_affricate", "不送气龈腭塞擦音；普通话 j。", "affricate", (3500, 9500), "j"),
    Segment(13, "[t͡ɕʰ]", "q_aspirated_alveolopalatal_affricate", "送气龈腭塞擦音；普通话 q。", "aspirated_affricate", (3500, 9500), "q"),
    Segment(14, "[ɕ]", "x_alveolopalatal_fricative", "龈腭擦音；普通话 x。", "fricative", (3500, 10000), "x"),
    Segment(15, "[t͡ʂ]", "zh_unaspirated_retroflex_affricate", "不送气卷舌塞擦音；普通话 zh。", "affricate", (1800, 6500), "zh"),
    Segment(16, "[t͡ʂʰ]", "ch_aspirated_retroflex_affricate", "送气卷舌塞擦音；普通话 ch。", "aspirated_affricate", (1800, 6500), "ch"),
    Segment(17, "[ʂ]", "sh_retroflex_fricative", "卷舌擦音；普通话 sh。", "fricative", (1800, 6500), "sh"),
    Segment(18, "[ɻ]", "r_retroflex_approximant", "卷舌近音；普通话 r 的一种宽式分析。", "sonorant", (450, 1300, 1600, 3000), "r"),
    Segment(19, "[ts]", "z_unaspirated_alveolar_affricate", "不送气齿龈塞擦音；普通话 z。", "affricate", (4000, 10000), "z"),
    Segment(20, "[tsʰ]", "c_aspirated_alveolar_affricate", "送气齿龈塞擦音；普通话 c。", "aspirated_affricate", (4000, 10000), "c"),
    Segment(21, "[s]", "s_alveolar_fricative", "齿龈擦音；普通话 s。", "fricative", (4000, 10000), "s"),
    Segment(22, "[ŋ]", "ng_velar_nasal", "软腭鼻音；普通话后鼻音韵尾 ng。", "sonorant", (300, 900, 2300, 3400), "ng"),
    Segment(23, "[j]", "i_glide", "硬腭近音；普通话 i 类介音。", "sonorant", (280, 2300, 3100, 3800), "i/y"),
    Segment(24, "[w]", "u_glide", "唇软腭近音；普通话 u 类介音。", "sonorant", (300, 750, 2200, 3200), "u/w"),
    Segment(25, "[a]", "a_open_front_vowel", "开前不圆唇元音。", "vowel", (850, 1500, 2500, 3500), "a"),
    Segment(26, "[ɑ]", "ang_back_a_vowel", "偏后的开元音；常见于 ang 等宽式/窄式说明。", "vowel", (750, 1150, 2600, 3500), "ang"),
    Segment(27, "[o]", "o_close_mid_back_rounded_vowel", "半闭后圆唇元音；普通话 o 的宽式目标。", "vowel", (500, 900, 2400, 3300), "o"),
    Segment(28, "[ɤ]", "e_back_unrounded_vowel", "后不圆唇元音；普通话 e 的常见宽式写法。", "vowel", (460, 1150, 2600, 3400), "e"),
    Segment(29, "[e]", "ei_close_mid_front_vowel", "半闭前不圆唇元音；出现在 ei 等复合韵母分析中。", "vowel", (400, 2100, 2700, 3600), "ei"),
    Segment(30, "[ə]", "schwa_mid_central_vowel", "央元音；用于 en/eng 等宽式分析。", "vowel", (500, 1500, 2500, 3500), "en"),
    Segment(31, "[ɛ]", "ie_open_mid_front_vowel", "半开前不圆唇元音；用于 ie/ian 等分析。", "vowel", (650, 1900, 2600, 3500), "ie"),
    Segment(32, "[i]", "i_close_front_unrounded_vowel", "闭前不圆唇元音；普通话 i。", "vowel", (300, 2500, 3200, 3800), "i"),
    Segment(33, "[u]", "u_close_back_rounded_vowel", "闭后圆唇元音；普通话 u。", "vowel", (350, 800, 2200, 3200), "u"),
    Segment(34, "[ʊ]", "ong_near_close_back_rounded_vowel", "近闭后圆唇元音；用于 ong/iong 等细化分析。", "vowel", (450, 1000, 2300, 3200), "ong"),
    Segment(35, "[y]", "u_umlaut_close_front_rounded_vowel", "闭前圆唇元音；普通话 ü。", "vowel", (300, 1900, 2400, 3300), "ü"),
    Segment(36, "[ɚ]", "er_r_colored_vowel", "卷舌/儿化元音；普通话 er。", "vowel", (500, 1300, 1600, 3200), "er"),
    Segment(37, "[ɿ]", "zi_apical_alveolar_vowel", "舌尖前元音；zi/ci/si 后的 i。", "vowel", (300, 1700, 2600, 3500), "zi"),
    Segment(38, "[ʅ]", "zhi_apical_retroflex_vowel", "舌尖后/卷舌类舌尖元音；zhi/chi/shi/ri 后的 i。", "vowel", (300, 1300, 2100, 3200), "zhi"),
]


def require_tools() -> None:
    if not PRAAT.exists():
        raise FileNotFoundError(f"找不到 Praat 命令行入口：{PRAAT}")
    if not FFMPEG or not Path(FFMPEG).exists():
        raise FileNotFoundError("找不到 ffmpeg，无法转 MP3。")


def quote_praat_path(path: Path) -> str:
    return str(path).replace('"', '""')


def vowel_script(segment: Segment, wav_path: Path) -> str:
    f1, f2, f3, f4 = segment.params
    return f"""
Create KlattGrid from vowel: "{segment.filename_stem}", 0.45, 150, {f1}, 80, {f2}, 90, {f3}, 120, {f4}, 180, 50
To Sound
Scale peak: 0.82
Save as WAV file: "{quote_praat_path(wav_path)}"
"""


def sonorant_script(segment: Segment, wav_path: Path) -> str:
    f1, f2, f3, f4 = segment.params
    return f"""
Create KlattGrid from vowel: "{segment.filename_stem}", 0.34, 135, {f1}, 100, {f2}, 120, {f3}, 150, {f4}, 220, 50
To Sound
Scale peak: 0.62
Save as WAV file: "{quote_praat_path(wav_path)}"
"""


def noise_env(duration: float, attack: float = 0.012, release: float = 0.018) -> str:
    return (
        f"(if x < {attack} then x/{attack} "
        f"else if x > {duration - release} then ({duration}-x)/{release} "
        "else 1 fi fi)"
    )


def noisy_formula(duration: float, start: float, end: float, amplitude: float = 0.12) -> str:
    env = noise_env(duration)
    return (
        f"if x < {start} or x > {end} then 0 "
        f"else {amplitude}*{env}*randomGauss(0,1) fi"
    )


def consonant_script(segment: Segment, wav_path: Path) -> str:
    low, high = segment.params
    if segment.kind == "fricative":
        duration = 0.34
        formula = noisy_formula(duration, 0.015, 0.325, 0.10)
    elif segment.kind == "stop":
        duration = 0.18
        formula = noisy_formula(duration, 0.045, 0.075, 0.18)
    elif segment.kind == "aspirated_stop":
        duration = 0.25
        formula = (
            f"if x < 0.045 or x > 0.175 then 0 "
            "else if x < 0.078 then 0.20*randomGauss(0,1) "
            "else 0.10*randomGauss(0,1) fi fi"
        )
    elif segment.kind == "affricate":
        duration = 0.25
        formula = noisy_formula(duration, 0.045, 0.185, 0.13)
    elif segment.kind == "aspirated_affricate":
        duration = 0.32
        formula = noisy_formula(duration, 0.045, 0.255, 0.13)
    else:
        raise ValueError(f"unsupported consonant kind: {segment.kind}")
    return f"""
Create Sound from formula: "{segment.filename_stem}", 1, 0, {duration}, {SAMPLE_RATE}, "{formula}"
Filter (pass Hann band): {low}, {high}, 100
Scale peak: 0.78
Save as WAV file: "{quote_praat_path(wav_path)}"
"""


def praat_script(segment: Segment, wav_path: Path) -> str:
    if segment.kind == "vowel":
        return vowel_script(segment, wav_path)
    if segment.kind == "sonorant":
        return sonorant_script(segment, wav_path)
    return consonant_script(segment, wav_path)


def run_praat(script_text: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".praat", encoding="utf-8", delete=False) as file:
        file.write(script_text)
        script_path = Path(file.name)
    try:
        subprocess.run([str(PRAAT), "--run", str(script_path)], check=True)
    finally:
        script_path.unlink(missing_ok=True)


def convert_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    subprocess.run(
        [
            str(FFMPEG),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "3",
            str(mp3_path),
        ],
        check=True,
    )


def write_readme() -> None:
    README_PATH.write_text(
        """Praat IPA single-sound preview pack

This folder contains generated listening previews for Mandarin IPA single sounds.
These files are not human IPA chart recordings and are not authoritative phonetic
targets. They are synthetic demos made with Praat for quick listening review.

Stops and affricates are generated as release/frication noises without a full
carrier syllable, so some items will naturally sound short or artificial.
Tone and full compound finals are intentionally not generated as fake single
sounds.

Nothing in this folder is connected to the Anki deck yet.
""",
        encoding="utf-8",
    )


def write_manifest(rows: list[dict[str, str]]) -> None:
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as file:
        fieldnames = ["filename", "ipa", "pinyin", "description", "generator", "notes"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_zip() -> None:
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(README_PATH, README_PATH.name)
        archive.write(MANIFEST_PATH, MANIFEST_PATH.name)
        for path in sorted(MP3_DIR.glob("*.mp3")):
            archive.write(path, f"mp3/{path.name}")


def main() -> None:
    require_tools()
    WAV_DIR.mkdir(parents=True, exist_ok=True)
    MP3_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    for segment in SEGMENTS:
        wav_path = WAV_DIR / f"{segment.filename_stem}.wav"
        mp3_path = MP3_DIR / f"{segment.filename_stem}.mp3"
        run_praat(praat_script(segment, wav_path))
        convert_to_mp3(wav_path, mp3_path)
        rows.append(
            {
                "filename": mp3_path.name,
                "ipa": segment.ipa,
                "pinyin": segment.pinyin,
                "description": segment.description,
                "generator": "Praat 6.4.65 KlattGrid/Sound formula + ffmpeg MP3",
                "notes": "Synthetic preview only; not connected to Anki deck.",
            }
        )

    write_manifest(rows)
    write_readme()
    write_zip()
    print(f"generated {len(rows)} MP3 files")
    print(f"mp3 directory: {MP3_DIR}")
    print(f"zip: {ZIP_PATH}")


if __name__ == "__main__":
    main()
