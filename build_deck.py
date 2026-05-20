#!/usr/bin/env python3
"""Build an Anki deck for Mandarin IPA and phonetics.

Run from this directory:
    python build_deck.py
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import csv
from pathlib import Path
from typing import Any, Iterable

import genanki
from genanki.note import _fix_deprecated_builtin_models_and_warn


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
MEDIA_DIR = PROJECT_DIR / "media"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_PATH = OUTPUT_DIR / "Chinese_IPA_Mandarin.apkg"
OUTPUT_ATTRIBUTION_PATH = OUTPUT_DIR / "audio_attribution.csv"
MEDIA_MANIFEST_PATH = MEDIA_DIR / "audio_manifest.csv"
VARIETY_SLUG = "mandarin"
INCLUDE_AUDIO = True
STABLE_ID_EPOCH_MS = 1_779_235_200_000  # 2026-05-20T00:00:00Z
STABLE_ID_HASH_SPAN_MS = 30 * 24 * 60 * 60 * 1000

DECK_IDS = {
    "ipa_consonant": 2051702801,
    "ipa_semivowel_syllabic": 2051702802,
    "ipa_vowel": 2051702803,
    "ipa_diphthong_rhotic": 2051702804,
    "ipa_tone": 2051702805,
    "concept_basics": 2051702711,
    "concept_articulation": 2051702712,
    "concept_mandarin": 2051702713,
}
MODEL_IDS = {
    "ipa_to_pinyin": 2051702602,
    "concept": 2051702605,
}

ROOT_DECK_NAME = "IPA · 普通话"
SUBDECK_NAMES = {
    "ipa_consonant": f"{ROOT_DECK_NAME}::01 IPA 识别::01 辅音",
    "ipa_semivowel_syllabic": f"{ROOT_DECK_NAME}::01 IPA 识别::02 半元音与音节辅音",
    "ipa_vowel": f"{ROOT_DECK_NAME}::01 IPA 识别::03 元音",
    "ipa_diphthong_rhotic": f"{ROOT_DECK_NAME}::01 IPA 识别::04 双元音与儿化",
    "ipa_tone": f"{ROOT_DECK_NAME}::01 IPA 识别::05 声调",
    "concept_basics": f"{ROOT_DECK_NAME}::02 语音学概念::01 读表基础",
    "concept_articulation": f"{ROOT_DECK_NAME}::02 语音学概念::02 音段类型",
    "concept_mandarin": f"{ROOT_DECK_NAME}::02 语音学概念::03 普通话重点",
}

MODEL_BY_DECK = {
    "ipa_consonant": "ipa_to_pinyin",
    "ipa_semivowel_syllabic": "ipa_to_pinyin",
    "ipa_vowel": "ipa_to_pinyin",
    "ipa_diphthong_rhotic": "ipa_to_pinyin",
    "ipa_tone": "ipa_to_pinyin",
    "concept_basics": "concept",
    "concept_articulation": "concept",
    "concept_mandarin": "concept",
}

CONCEPT_DECK_BY_NAME = {
    "IPA 表格的用途": "concept_basics",
    "斜线 / / 的读法": "concept_basics",
    "拼音不是 IPA": "concept_basics",
    "注音不是 IPA": "concept_basics",
    "范例音节怎么读": "concept_basics",
    "送气": "concept_articulation",
    "不送气": "concept_articulation",
    "塞音": "concept_articulation",
    "塞擦音": "concept_articulation",
    "擦音": "concept_articulation",
    "鼻音": "concept_articulation",
    "半元音": "concept_articulation",
    "音节辅音": "concept_articulation",
    "卷舌音": "concept_mandarin",
    "龈腭音": "concept_mandarin",
    "元音环境变体": "concept_mandarin",
    "拼音省写": "concept_mandarin",
    "轻声": "concept_mandarin",
    "第三声变调": "concept_mandarin",
    "儿化": "concept_mandarin",
}

FIELDS = [
    {"name": "Category"},
    {"name": "IPA"},
    {"name": "Pinyin"},
    {"name": "Hanzi"},
    {"name": "Example"},
    {"name": "Articulation"},
    {"name": "Explanation"},
    {"name": "CommonMisconception"},
    {"name": "Notes"},
    {"name": "Audio"},
    {"name": "Tags"},
]

CSS = """
.card {
  font-family: "Noto Sans", "Noto Sans CJK SC", "Charis SIL", "Doulos SIL", "Arial Unicode MS", sans-serif;
  font-size: 20px;
  line-height: 1.55;
  color: #18202a;
  background: #fbfaf7;
  text-align: left;
}
.card.nightMode,
.nightMode .card {
  color: #ece7dc;
  background: #171717;
}
.wrap {
  max-width: 760px;
  margin: 0 auto;
  padding: 28px 24px;
}
.category {
  display: inline-block;
  margin-bottom: 18px;
  padding: 2px 8px;
  border: 1px solid #c9c3b6;
  border-radius: 6px;
  color: #5e5a50;
  font-size: 13px;
  letter-spacing: 0;
  text-transform: uppercase;
}
.ipa {
  font-family: "Charis SIL", "Doulos SIL", "Noto Sans", "Noto Sans CJK SC", "Arial Unicode MS", sans-serif;
  font-size: 52px;
  line-height: 1.15;
  margin: 4px 0 16px;
}
.concept {
  font-size: 38px;
  font-weight: 700;
  margin: 6px 0 18px;
}
.prompt {
  color: #3a4653;
  font-size: 21px;
}
.nightMode .prompt {
  color: #c9c2b6;
}
hr#answer {
  border: 0;
  border-top: 1px solid #d9d3c7;
  margin: 24px 0;
}
.nightMode hr#answer {
  border-top-color: #3f3a33;
}
.row {
  margin: 10px 0;
}
.label {
  color: #686257;
  font-weight: 700;
  margin-right: 0.35em;
}
.answer-ipa {
  font-family: "Charis SIL", "Doulos SIL", "Noto Sans", "Noto Sans CJK SC", "Arial Unicode MS", sans-serif;
  font-size: 30px;
}
.note {
  color: #4b5563;
}
.nightMode .note {
  color: #b8b2a8;
}
.misconception {
  color: #7a342b;
}
.nightMode .misconception {
  color: #f0a69a;
}
.audio {
  margin-top: 12px;
}
.audio-line {
  margin: 8px 0;
}
.audio-unit {
  display: inline-block;
  min-width: 5.5em;
  font-family: "Charis SIL", "Doulos SIL", "Noto Sans", "Noto Sans CJK SC", "Arial Unicode MS", sans-serif;
  font-size: 22px;
}
.audio-note {
  margin-top: 4px;
  color: #686257;
  font-size: 14px;
}
.nightMode .audio-note {
  color: #b8b2a8;
}
.nightMode .label {
  color: #d3c6b4;
}
"""

TEMPLATE_IPA_TO_PINYIN = {
    "name": "IPA 识别",
    "qfmt": """
<div class="wrap">
  <div class="ipa">{{IPA}}</div>
</div>
""",
    "afmt": """
<div class="wrap">
  <div class="ipa">{{IPA}}</div>
  {{#Audio}}
  <div class="audio">{{Audio}}</div>
  {{/Audio}}
</div>
<hr id="answer">
<div class="wrap">
  <div class="row"><span class="label">拼音：</span>{{Pinyin}}</div>
  <div class="row"><span class="label">例字：</span>{{Hanzi}}</div>
  <div class="row"><span class="label">例词/短语：</span>{{Example}}</div>
  <div class="row"><span class="label">发音说明：</span>{{Articulation}}</div>
  <div class="row">{{Explanation}}</div>
  <div class="row misconception"><span class="label">易混点：</span>{{CommonMisconception}}</div>
  <div class="row note"><span class="label">补充：</span>{{Notes}}</div>
</div>
""",
}

TEMPLATE_CONCEPT = {
    "name": "概念例子",
    "qfmt": """
<div class="wrap">
  <div class="concept">{{IPA}}</div>
</div>
""",
    "afmt": """
<div class="wrap">
  <div class="concept">{{IPA}}</div>
  {{#Audio}}
  <div class="audio">{{Audio}}</div>
  {{/Audio}}
</div>
<hr id="answer">
<div class="wrap">
  <div class="row"><span class="label">简明定义：</span>{{Explanation}}</div>
  <div class="row"><span class="label">IPA 例子：</span><span class="answer-ipa">{{Pinyin}}</span></div>
  <div class="row"><span class="label">普通话例子：</span>{{Example}}</div>
  <div class="row"><span class="label">为什么重要：</span>{{Articulation}}</div>
  <div class="row misconception"><span class="label">易混点：</span>{{CommonMisconception}}</div>
  <div class="row note"><span class="label">补充：</span>{{Notes}}</div>
</div>
""",
}

REQUIRED_FIELDS = {
    "initials.json": [
        "pinyin",
        "ipa",
        "example_hanzi",
        "example_word",
        "articulation",
        "explanation_for_native_chinese",
        "common_misconception",
        "notes",
        "tags",
    ],
    "finals.json": [
        "final",
        "ipa",
        "example_hanzi",
        "example_word",
        "explanation_for_native_chinese",
        "common_misconception",
        "notes",
        "tags",
    ],
    "tones.json": [
        "tone_number",
        "tone_name_cn",
        "contour",
        "ipa_tone_letters",
        "example",
        "example_hanzi",
        "example_word",
        "explanation_for_native_chinese",
        "common_misconception",
        "notes",
    ],
    "contrasts.json": [
        "ipa_a",
        "pinyin_a",
        "example_a",
        "ipa_b",
        "pinyin_b",
        "example_b",
        "core_difference",
        "explanation_for_native_chinese",
        "common_misconception",
        "tags",
    ],
    "concepts.json": [
        "concept",
        "simple_definition",
        "mandarin_examples",
        "ipa_examples",
        "why_it_matters_for_native_chinese",
        "common_misconception",
        "tags",
    ],
}

AUDIO_EXTENSIONS = {".mp3"}
MEDIA_MANIFEST_FIELDS = [
    "filename",
    "source_project",
    "source_title",
    "source_url",
    "author",
    "license",
    "license_url",
    "notes",
]
REQUIRED_MEDIA_MANIFEST_FIELDS = [
    "filename",
    "source_project",
    "source_title",
    "source_url",
    "author",
    "license",
    "license_url",
]

IPA_AUDIO_STEMS = {
    "[p]": "ipa_p",
    "[pʰ]": "ipa_p_aspirated",
    "[t]": "ipa_t",
    "[tʰ]": "ipa_t_aspirated",
    "[k]": "ipa_k",
    "[kʰ]": "ipa_k_aspirated",
    "[m]": "ipa_m",
    "[m̥]": "ipa_m_voiceless",
    "[m̩]": "ipa_syllabic_m",
    "[n]": "ipa_n",
    "[nʲ]": "ipa_n_palatalized",
    "[n̩]": "ipa_syllabic_n",
    "[ŋ]": "ipa_eng",
    "[ŋ̊]": "ipa_eng_voiceless",
    "[ŋ̍]": "ipa_syllabic_eng",
    "[l]": "ipa_l",
    "[f]": "ipa_f",
    "[x]": "ipa_x",
    "[h]": "ipa_h",
    "[t͡ɕ]": "ipa_t_alveolopalatal_affricate",
    "[t͡ɕʰ]": "ipa_t_alveolopalatal_affricate_aspirated",
    "[ɕ]": "ipa_alveolopalatal_sibilant",
    "[t͡ʂ]": "ipa_t_retroflex_affricate",
    "[t͡ʂʰ]": "ipa_t_retroflex_affricate_aspirated",
    "[ʈ͡ʂ]": "ipa_t_retroflex_affricate",
    "[ʈ͡ʂʰ]": "ipa_t_retroflex_affricate_aspirated",
    "[ʂ]": "ipa_retroflex_sibilant",
    "[ts]": "ipa_ts",
    "[tsʰ]": "ipa_ts_aspirated",
    "[t͡s]": "ipa_ts",
    "[t͡sʰ]": "ipa_ts_aspirated",
    "[s]": "ipa_s",
    "[z]": "ipa_z",
    "[ɻ]": "ipa_retroflex_approximant",
    "[ʐ]": "ipa_retroflex_sibilant_voiced",
    "[ʔ]": "ipa_glottal_stop",
    "[j]": "ipa_j",
    "[ɉ]": "ipa_j_stroked",
    "[w]": "ipa_w",
    "[ɥ]": "ipa_labiopalatal_approximant",
    "[ɹ̩]": "ipa_syllabic_alveolar_approximant",
    "[ɻ̩]": "ipa_syllabic_retroflex_approximant",
    "∅": "ipa_zero",
    "[a]": "ipa_a",
    "[ä]": "ipa_a_central",
    "[ɑ]": "ipa_alpha",
    "[e̞]": "ipa_e_lowered",
    "[o]": "ipa_o",
    "[o̞]": "ipa_o_lowered",
    "[o̞˞]": "ipa_o_lowered_rhotic",
    "[ɤ]": "ipa_gamma",
    "[ɤ̞]": "ipa_gamma_lowered",
    "[ɤ˞]": "ipa_gamma_rhotic",
    "[ə]": "ipa_schwa",
    "[ɛ]": "ipa_epsilon",
    "[œ̜]": "ipa_oe_less_rounded",
    "[i]": "ipa_i",
    "[u]": "ipa_u",
    "[u˞]": "ipa_u_rhotic",
    "[ʊ]": "ipa_upsilon",
    "[ʊ̃˞]": "ipa_upsilon_nasalized_rhotic",
    "[y]": "ipa_y",
    "[ai]": "ipa_ai",
    "[ai̯]": "ipa_ai",
    "[ei]": "ipa_ei",
    "[ei̯]": "ipa_ei",
    "[au]": "ipa_au",
    "[ou]": "ipa_ou",
    "[ou̯]": "ipa_ou",
    "[ou̯˞]": "ipa_ou_rhotic",
    "[an]": "ipa_an",
    "[ən]": "ipa_schwa_n",
    "[ɑŋ]": "ipa_alpha_eng",
    "[əŋ]": "ipa_schwa_eng",
    "[ʊŋ]": "ipa_upsilon_eng",
    "[ja]": "ipa_ja",
    "[jɛ]": "ipa_j_epsilon",
    "[jau]": "ipa_jau",
    "[jou]": "ipa_jou",
    "[jɛn]": "ipa_j_epsilon_n",
    "[in]": "ipa_in",
    "[jɑŋ]": "ipa_j_alpha_eng",
    "[iŋ]": "ipa_i_eng",
    "[jʊŋ]": "ipa_j_upsilon_eng",
    "[wa]": "ipa_wa",
    "[wo]": "ipa_wo",
    "[wai]": "ipa_wai",
    "[wei]": "ipa_wei",
    "[wan]": "ipa_wan",
    "[wən]": "ipa_w_schwa_n",
    "[wɑŋ]": "ipa_w_alpha_eng",
    "[wəŋ]": "ipa_w_schwa_eng",
    "[yɛ]": "ipa_y_epsilon",
    "[yɛn]": "ipa_y_epsilon_n",
    "[yn]": "ipa_y_n",
    "[ɚ]": "ipa_er",
    "[ɚ̃]": "ipa_er_nasalized",
    "[äɚ̯]": "ipa_a_central_er",
    "[ä̃ɚ̯̃]": "ipa_a_central_nasal_er",
    "[ɐɚ̯]": "ipa_turned_a_er",
    "[ɑu̯]": "ipa_alpha_u",
    "[ɑu̯˞]": "ipa_alpha_u_rhotic",
    "[ɿ]": "ipa_apical_alveolar_vowel",
    "[ʅ]": "ipa_apical_retroflex_vowel",
    "[˥]": "ipa_tone_1",
    "[˧˥]": "ipa_tone_2",
    "[˨˩˦]": "ipa_tone_3",
    "[˥˩]": "ipa_tone_4",
}

TONE_TEXT_AUDIO_STEMS = {
    "˨˩˦": "ipa_tone_3",
    "˧˥": "ipa_tone_2",
    "˥˩": "ipa_tone_4",
    "˥": "ipa_tone_1",
}

PINYIN_OUTSIDE_IPA_RE = re.compile(
    r"[A-Za-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜüÜńňǹḿ]+"
)


def stable_audio_stem(prefix: str, display: Any) -> str:
    digest = hashlib.sha1(str(display).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


INITIAL_LEVELS = {
    "b": 1,
    "p": 1,
    "m": 1,
    "f": 1,
    "d": 1,
    "t": 1,
    "n": 1,
    "l": 1,
    "g": 1,
    "k": 1,
    "h": 1,
    "零声母": 1,
    "z": 2,
    "c": 2,
    "s": 2,
    "zh": 2,
    "ch": 2,
    "sh": 2,
    "r": 2,
    "j": 2,
    "q": 2,
    "x": 2,
}

FINAL_LEVELS = {
    "a": 1,
    "i": 1,
    "u": 1,
    "ai": 1,
    "ei": 1,
    "ao": 1,
    "ou": 1,
    "an": 1,
    "en": 1,
    "ang": 1,
    "eng": 1,
    "o": 2,
    "e": 2,
    "ü": 2,
    "ong": 2,
    "ia": 2,
    "ie": 2,
    "iao": 2,
    "ian": 2,
    "in": 2,
    "iang": 2,
    "ing": 2,
    "ua": 2,
    "uo": 2,
    "uai": 2,
    "uan": 2,
    "uang": 2,
    "iu": 3,
    "ui": 3,
    "un": 3,
    "ueng": 3,
    "iong": 3,
    "üe": 3,
    "üan": 3,
    "ün": 3,
    "er": 3,
    "i (zi/ci/si)": 3,
    "i (zhi/chi/shi/ri)": 3,
}

CONCEPT_LEVELS = {
    "IPA 是什么": 1,
    "宽式标音": 1,
    "拼音不是 IPA": 1,
    "声母": 1,
    "韵母": 1,
    "声调": 1,
    "送气": 1,
    "不送气": 1,
    "清音": 1,
    "浊音": 1,
    "塞音": 1,
    "窄式标音": 2,
    "塞擦音": 2,
    "擦音": 2,
    "鼻音": 2,
    "边音": 2,
    "卷舌音": 2,
    "龈腭音": 2,
    "前鼻音韵尾": 2,
    "后鼻音韵尾": 2,
    "舌尖元音": 3,
    "轻声": 3,
    "第三声变调": 3,
    "儿化": 3,
}


def difficulty_tags(category: str, item: dict[str, Any]) -> list[str]:
    if category == "initial":
        level = INITIAL_LEVELS.get(str(item["pinyin"]), 2)
    elif category == "final":
        level = FINAL_LEVELS.get(str(item["final"]), 2)
    elif category == "tone":
        level = 2 if int(item["tone_number"]) in {3, 5} else 1
    elif category == "concept":
        level = CONCEPT_LEVELS.get(str(item["concept"]), 2)
    elif category == "contrast":
        tags = set(item.get("tags", []))
        if tags & {"apical_vowel", "rhotic", "spelling_abbreviation", "tone_sandhi"}:
            level = 3
        elif tags & {"retroflex", "alveolo-palatal", "front_nasal", "back_nasal", "front_rounded", "tone"}:
            level = 2
        else:
            level = 1
    else:
        level = 2
    return [f"level:{level}"]


def initial_deck_key(item: dict[str, Any]) -> str:
    tags = set(normalize_tags(item.get("tags", [])))
    if "semivowel" in tags or "syllabic_consonant" in tags:
        return "ipa_semivowel_syllabic"
    return "ipa_consonant"


def final_deck_key(item: dict[str, Any]) -> str:
    tags = set(normalize_tags(item.get("tags", [])))
    if "diphthong" in tags or "rhotic" in tags:
        return "ipa_diphthong_rhotic"
    return "ipa_vowel"


def load_json_file(filename: str) -> list[dict[str, Any]]:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"缺少数据文件：{path}")
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{filename} 顶层必须是 JSON 数组。")
    validate_items(filename, data)
    return data


def validate_items(filename: str, items: list[dict[str, Any]]) -> None:
    required = REQUIRED_FIELDS[filename]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{filename} 第 {index} 项必须是对象。")
        missing = [field for field in required if field not in item]
        empty = [
            field
            for field in required
            if field in item and item[field] in ("", None, [])
        ]
        if missing or empty:
            details = []
            if missing:
                details.append(f"缺字段：{', '.join(missing)}")
            if empty:
                details.append(f"字段为空：{', '.join(empty)}")
            raise ValueError(f"{filename} 第 {index} 项数据不完整；" + "；".join(details))
        tags = item.get("tags")
        if tags is not None and not isinstance(tags, list):
            raise ValueError(f"{filename} 第 {index} 项的 tags 必须是数组。")
        if filename in {"initials.json", "finals.json", "tones.json"}:
            example_word = str(item.get("example_word", ""))
            outside_ipa = re.sub(r"/[^/]+/", "", example_word)
            if PINYIN_OUTSIDE_IPA_RE.search(outside_ipa):
                raise ValueError(
                    f"{filename} 第 {index} 项 example_word 不应含拼音；"
                    "请写成“例词 /IPA/”。"
                )


def make_model(model_id: int, name: str, template: dict[str, str]) -> genanki.Model:
    return genanki.Model(
        model_id,
        name,
        fields=FIELDS,
        templates=[template],
        css=CSS,
        sort_field_index=1,
    )


def stable_guid(*parts: Any) -> str:
    raw = "|".join(str(part) for part in parts)
    return "mipa-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


def stable_int_id(kind: str, *parts: Any) -> int:
    raw = "|".join([kind, *(str(part) for part in parts)])
    digest = int(hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14], 16)
    return STABLE_ID_EPOCH_MS + (digest % STABLE_ID_HASH_SPAN_MS)


def text_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "<br>".join(html.escape(str(item)) for item in value)
    if isinstance(value, dict):
        rows = []
        for key, item in value.items():
            rows.append(f"<b>{html.escape(str(key))}</b>: {html.escape(str(item))}")
        return "<br>".join(rows)
    return html.escape(str(value)).replace("\n", "<br>")


def clean_tag(tag: str) -> str:
    tag = str(tag).strip().replace(" ", "_")
    tag = re.sub(r"[^\w\u4e00-\u9fff:.-]+", "_", tag)
    return tag.strip("_")


def normalize_tags(*tag_groups: Iterable[str] | str | None) -> list[str]:
    tags: list[str] = []
    for group in tag_groups:
        if group is None:
            continue
        if isinstance(group, str):
            candidates = [group]
        else:
            candidates = list(group)
        for tag in candidates:
            cleaned = clean_tag(tag)
            if cleaned and cleaned not in tags:
                tags.append(cleaned)
    return tags


def safe_media_key(value: Any) -> str:
    value = str(value).strip().lower()
    replacements = {
        "ü": "v",
        "∅": "zero",
        "零声母": "zero",
        "/": "_",
        " ": "_",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"[^a-z0-9_\-\u4e00-\u9fff]+", "_", value)
    return value.strip("_")


def ipa_audio_candidates(ipa: Any) -> list[str]:
    stem = IPA_AUDIO_STEMS.get(str(ipa))
    return [stem] if stem else [stable_audio_stem("ipa", ipa)]


def collect_media_files() -> tuple[list[str], dict[str, Path]]:
    MEDIA_DIR.mkdir(exist_ok=True)
    media_paths = [
        path
        for path in sorted(MEDIA_DIR.rglob("*"))
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    by_basename: dict[str, Path] = {}
    duplicates: dict[str, list[Path]] = {}
    for path in media_paths:
        if path.name in by_basename:
            duplicates.setdefault(path.name, [by_basename[path.name]]).append(path)
        by_basename[path.name] = path
    if duplicates:
        joined = "; ".join(
            f"{name}: {', '.join(str(path) for path in paths)}"
            for name, paths in duplicates.items()
        )
        raise ValueError(f"media/ 中存在同名音频文件，Anki 打包会冲突：{joined}")
    return [str(path) for path in media_paths], by_basename


def load_audio_manifest(media_by_basename: dict[str, Path]) -> dict[str, dict[str, str]]:
    if not MEDIA_MANIFEST_PATH.exists():
        if media_by_basename:
            raise FileNotFoundError(
                f"media/ 中有音频文件，但缺少来源清单：{MEDIA_MANIFEST_PATH}"
            )
        return {}

    with MEDIA_MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return {}
        missing_columns = [
            field
            for field in REQUIRED_MEDIA_MANIFEST_FIELDS
            if field not in reader.fieldnames
        ]
        if missing_columns:
            raise ValueError(
                "media/audio_manifest.csv 缺少列："
                + ", ".join(missing_columns)
            )

        rows: dict[str, dict[str, str]] = {}
        for line_number, row in enumerate(reader, start=2):
            if not row or not any((value or "").strip() for value in row.values()):
                continue
            filename = Path((row.get("filename") or "").strip()).name
            normalized = {
                field: (row.get(field) or "").strip()
                for field in MEDIA_MANIFEST_FIELDS
            }
            normalized["filename"] = filename
            missing_values = [
                field
                for field in REQUIRED_MEDIA_MANIFEST_FIELDS
                if not normalized.get(field)
            ]
            if missing_values:
                raise ValueError(
                    f"media/audio_manifest.csv 第 {line_number} 行缺少值："
                    + ", ".join(missing_values)
                )
            if filename in rows:
                raise ValueError(
                    f"media/audio_manifest.csv 中重复登记了音频文件：{filename}"
                )
            rows[filename] = normalized

    media_names = set(media_by_basename)
    manifest_names = set(rows)
    missing_manifest = sorted(media_names - manifest_names)
    orphan_manifest = sorted(manifest_names - media_names)
    if missing_manifest:
        raise ValueError(
            "以下 media/ 音频文件缺少 audio_manifest.csv 记录："
            + ", ".join(missing_manifest)
        )
    if orphan_manifest:
        raise ValueError(
            "audio_manifest.csv 登记了不存在的音频文件："
            + ", ".join(orphan_manifest)
        )
    return rows


def write_audio_attribution(manifest_rows: dict[str, dict[str, str]]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    with OUTPUT_ATTRIBUTION_PATH.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=MEDIA_MANIFEST_FIELDS)
        writer.writeheader()
        for filename in sorted(manifest_rows):
            writer.writerow(manifest_rows[filename])


def audio_markup(filename: str, manifest_rows: dict[str, dict[str, str]] | None = None) -> str:
    markup = f"[sound:{filename}]"
    row = (manifest_rows or {}).get(filename, {})
    if row.get("source_project") == "Pinyin syllable demo":
        match = re.search(
            r"(?:mp3-chinese-pinyin-sound|pinyin syllable) ([^.\s]+)\.mp3",
            row.get("source_title", ""),
        )
        syllable = match.group(1) if match else "普通话音节"
        markup += (
            '<div class="audio-note">'
            f"示范音节：{html.escape(syllable)}（不是孤立 IPA 单音）"
            "</div>"
        )
    return markup


def audio_field(
    item: dict[str, Any],
    media_by_basename: dict[str, Path],
    candidates: Iterable[str],
    manifest_rows: dict[str, dict[str, str]] | None = None,
) -> str:
    explicit = item.get("audio")
    if explicit:
        filename = Path(str(explicit)).name
        if filename not in media_by_basename:
            raise FileNotFoundError(f"数据引用了音频 {filename}，但 media/ 中没有找到。")
        return audio_markup(filename, manifest_rows)

    for stem in candidates:
        stem = safe_media_key(stem)
        stems = [stem] if stem.startswith(f"{VARIETY_SLUG}_") else [f"{VARIETY_SLUG}_{stem}", stem]
        for candidate_stem in stems:
            for extension in AUDIO_EXTENSIONS:
                filename = f"{candidate_stem}{extension}"
                if filename in media_by_basename:
                    return audio_markup(filename, manifest_rows)
    return ""


def audio_for_ipa_units(
    ipa_display: str,
    media_by_basename: dict[str, Path],
    manifest_rows: dict[str, dict[str, str]],
    include_unbracketed_tones: bool = False,
) -> str:
    units = re.findall(r"\[[^\]]+\]|∅", ipa_display)
    if include_unbracketed_tones:
        for tone_text in TONE_TEXT_AUDIO_STEMS:
            if tone_text in ipa_display:
                units.append(tone_text)
    lines: list[str] = []
    seen: set[str] = set()
    for unit in units:
        if unit in seen:
            continue
        seen.add(unit)
        candidates = [TONE_TEXT_AUDIO_STEMS[unit]] if unit in TONE_TEXT_AUDIO_STEMS else ipa_audio_candidates(unit)
        sound = audio_field({}, media_by_basename, candidates, manifest_rows)
        if sound:
            lines.append(
                f'<div class="audio-line"><span class="audio-unit">{text_field(unit)}</span>{sound}</div>'
            )
    return "".join(lines)


def fields_for_note(
    *,
    category: str,
    ipa: Any,
    pinyin: Any = "",
    hanzi: Any = "",
    example: Any = "",
    articulation: Any = "",
    explanation: Any = "",
    misconception: Any = "",
    notes: Any = "",
    audio: str = "",
    tags: Iterable[str] | str | None = None,
) -> list[str]:
    tag_list = normalize_tags(tags)
    return [
        text_field(category),
        text_field(ipa),
        text_field(pinyin),
        text_field(hanzi),
        text_field(example),
        text_field(articulation),
        text_field(explanation),
        text_field(misconception),
        text_field(notes),
        audio,
        text_field(" ".join(tag_list)),
    ]


class StableNote(genanki.Note):
    def __init__(
        self,
        *,
        note_id: int,
        seen_card_ids: set[int],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.note_id = note_id
        self.seen_card_ids = seen_card_ids

    def write_to_db(self, cursor, timestamp: float, deck_id, id_gen) -> None:  # type: ignore[no-untyped-def]
        self.fields = _fix_deprecated_builtin_models_and_warn(self.model, self.fields)
        self._check_number_model_fields_matches_num_fields()
        self._check_invalid_html_tags_in_fields()
        cursor.execute(
            "INSERT INTO notes VALUES(?,?,?,?,?,?,?,?,?,?,?);",
            (
                self.note_id,
                self.guid,
                self.model.model_id,
                int(timestamp),
                -1,
                self._format_tags(),
                self._format_fields(),
                self.sort_field,
                0,
                0,
                "",
            ),
        )

        for card in self.cards:
            card_id = stable_int_id("card", self.guid, card.ord)
            if card_id in self.seen_card_ids:
                raise ValueError(f"出现重复 card_id：{card_id}，来源：{self.guid}:{card.ord}")
            self.seen_card_ids.add(card_id)
            queue = -1 if card.suspend else 0
            cursor.execute(
                "INSERT INTO cards VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                (
                    card_id,
                    self.note_id,
                    deck_id,
                    card.ord,
                    int(timestamp),
                    -1,
                    0,
                    queue,
                    self.due,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    "",
                ),
            )


def add_note(
    deck: genanki.Deck,
    model: genanki.Model,
    fields: list[str],
    tags: list[str],
    guid_parts: tuple[Any, ...],
    seen_guids: set[str],
    seen_note_ids: set[int],
    seen_card_ids: set[int],
) -> None:
    guid = stable_guid(*guid_parts)
    if guid in seen_guids:
        raise ValueError(f"出现重复 GUID：{guid}，来源：{guid_parts}")
    seen_guids.add(guid)
    note_id = stable_int_id("note", guid)
    if note_id in seen_note_ids:
        raise ValueError(f"出现重复 note_id：{note_id}，来源：{guid_parts}")
    seen_note_ids.add(note_id)
    deck.add_note(
        StableNote(
            model=model,
            fields=fields,
            tags=tags,
            guid=guid,
            note_id=note_id,
            seen_card_ids=seen_card_ids,
        )
    )


def build_deck() -> tuple[int, int, int]:
    initials = load_json_file("initials.json")
    finals = load_json_file("finals.json")
    tones = load_json_file("tones.json")
    concepts = load_json_file("concepts.json")

    if INCLUDE_AUDIO:
        media_files, media_by_basename = collect_media_files()
        audio_manifest_rows = load_audio_manifest(media_by_basename)
    else:
        media_files = []
        media_by_basename = {}
        audio_manifest_rows = {}

    models = {
        "ipa_to_pinyin": make_model(
            MODEL_IDS["ipa_to_pinyin"],
            "IPA · 普通话 - IPA 识别",
            TEMPLATE_IPA_TO_PINYIN,
        ),
        "concept": make_model(
            MODEL_IDS["concept"],
            "IPA · 普通话 - 语音学概念",
            TEMPLATE_CONCEPT,
        ),
    }

    decks = {
        key: genanki.Deck(DECK_IDS[key], SUBDECK_NAMES[key])
        for key in SUBDECK_NAMES
    }
    seen_guids: set[str] = set()
    seen_note_ids: set[int] = set()
    seen_card_ids: set[int] = set()
    note_count = 0
    card_count = 0

    def add(
        deck_key: str,
        field_values: list[str],
        tags: list[str],
        guid_parts: tuple[Any, ...],
    ) -> None:
        nonlocal note_count, card_count
        model_key = MODEL_BY_DECK[deck_key]
        add_note(
            decks[deck_key],
            models[model_key],
            field_values,
            tags,
            guid_parts,
            seen_guids,
            seen_note_ids,
            seen_card_ids,
        )
        note_count += 1
        card_count += 1

    for item in initials:
        category = "initial"
        tags = normalize_tags(category, item["tags"], difficulty_tags(category, item))
        audio = ""
        if INCLUDE_AUDIO:
            audio = audio_for_ipa_units(
                text_field(item["ipa"]),
                media_by_basename,
                audio_manifest_rows,
            ) or audio_field(
                item,
                media_by_basename,
                ipa_audio_candidates(item["ipa"]),
                audio_manifest_rows,
            )
        common_fields = dict(
            category=category,
            ipa=item["ipa"],
            pinyin=item["pinyin"],
            hanzi=item["example_hanzi"],
            example=item["example_word"],
            articulation=item["articulation"],
            explanation=item["explanation_for_native_chinese"],
            misconception=item["common_misconception"],
            notes=item["notes"],
            audio=audio,
            tags=tags,
        )
        add(
            initial_deck_key(item),
            fields_for_note(**common_fields),
            normalize_tags(tags, "card:ipa_to_pinyin"),
            (category, "ipa_to_pinyin", item["pinyin"], item["ipa"]),
        )

    for item in finals:
        category = "final"
        final = item["final"]
        tags = normalize_tags(category, item["tags"], difficulty_tags(category, item))
        audio = ""
        if INCLUDE_AUDIO:
            audio = audio_for_ipa_units(
                text_field(item["ipa"]),
                media_by_basename,
                audio_manifest_rows,
            ) or audio_field(
                item,
                media_by_basename,
                ipa_audio_candidates(item["ipa"]),
                audio_manifest_rows,
            )
        articulation = item.get("articulation", "韵母；重点看主元音、介音和韵尾。")
        common_fields = dict(
            category=category,
            ipa=item["ipa"],
            pinyin=final,
            hanzi=item["example_hanzi"],
            example=item["example_word"],
            articulation=articulation,
            explanation=item["explanation_for_native_chinese"],
            misconception=item["common_misconception"],
            notes=item["notes"],
            audio=audio,
            tags=tags,
        )
        add(
            final_deck_key(item),
            fields_for_note(**common_fields),
            normalize_tags(tags, "card:ipa_to_pinyin"),
            (category, "ipa_to_pinyin", final, item["ipa"]),
        )

    for item in tones:
        category = "tone"
        tone_number = str(item["tone_number"])
        tags = normalize_tags(category, item.get("tags", []), f"tone:{tone_number}", difficulty_tags(category, item))
        audio = ""
        if INCLUDE_AUDIO:
            audio = audio_field(
                item,
                media_by_basename,
                [f"ipa_tone_{tone_number}", f"ipa_{safe_media_key(item['ipa_tone_letters'])}"],
                audio_manifest_rows,
            )
        ipa_display = f"{item['ipa_tone_letters']} ({item['contour']})"
        add(
            "ipa_tone",
            fields_for_note(
                category=category,
                ipa=ipa_display,
                pinyin=f"{item['tone_name_cn']} / 第{tone_number}声",
                hanzi=item.get("example_hanzi", item["example"]),
                example=item.get("example_word", item["example"]),
                articulation=f"声调轮廓：{item['contour']}",
                explanation=item["explanation_for_native_chinese"],
                misconception=item["common_misconception"],
                notes=item["notes"],
                audio=audio,
                tags=tags,
            ),
            normalize_tags(tags, "card:ipa_to_pinyin"),
            (category, "ipa_to_pinyin", tone_number, ipa_display),
        )

    for item in concepts:
        category = "concept"
        tags = normalize_tags(category, item["tags"], difficulty_tags(category, item))
        audio = ""
        if INCLUDE_AUDIO:
            audio = audio_field(
                item,
                media_by_basename,
                [f"concept_{item['concept']}"],
                audio_manifest_rows,
            )
            if not audio:
                audio = audio_for_ipa_units(
                    text_field(item["ipa_examples"]),
                    media_by_basename,
                    audio_manifest_rows,
                    include_unbracketed_tones=True,
                )
            if not audio and item["concept"] == "第三声变调":
                tone_lines = [
                    ("214（三声原调）", "ipa_tone_3"),
                    ("35（变调后）", "ipa_tone_2"),
                ]
                audio = "".join(
                    f'<div class="audio-line"><span class="audio-unit">{text_field(label)}</span>'
                    f"{audio_field({}, media_by_basename, [stem], audio_manifest_rows)}</div>"
                    for label, stem in tone_lines
                    if audio_field({}, media_by_basename, [stem], audio_manifest_rows)
                )
        deck_key = CONCEPT_DECK_BY_NAME.get(item["concept"], "concept_mandarin")
        add(
            deck_key,
            fields_for_note(
                category=category,
                ipa=item["concept"],
                pinyin=item["ipa_examples"],
                hanzi="",
                example=item["mandarin_examples"],
                articulation=item["why_it_matters_for_native_chinese"],
                explanation=item["simple_definition"],
                misconception=item["common_misconception"],
                notes=item.get("notes", "偏向帮助中文母语者读懂普通话 IPA，不追求覆盖所有语音学流派细节。"),
                audio=audio,
                tags=tags,
            ),
            normalize_tags(tags, "card:concept"),
            (category, "concept", item["concept"]),
        )

    OUTPUT_DIR.mkdir(exist_ok=True)
    write_audio_attribution(audio_manifest_rows)
    package = genanki.Package(list(decks.values()))
    package.media_files = media_files
    package.write_to_file(OUTPUT_PATH)

    return note_count, card_count, len(media_files)


def main() -> None:
    note_count, card_count, media_count = build_deck()
    print(f"卡组名: {ROOT_DECK_NAME}")
    print("子卡组:")
    for name in SUBDECK_NAMES.values():
        print(f"  - {name.split('::', 1)[1]}")
    print(f"note 数量: {note_count}")
    print(f"card 数量: {card_count}")
    print(f"输出路径: {OUTPUT_PATH}")
    print(f"media 文件数量: {media_count}")
    print(f"音频来源清单: {OUTPUT_ATTRIBUTION_PATH}")


if __name__ == "__main__":
    main()
