#!/usr/bin/env python3
"""Refresh card example words with IPA generated from the converter source data.

This script uses the open source data files from:
    https://github.com/nk2028/putonghua-ipa-converter

It writes only Chinese text plus IPA into data/*.json. Pinyin is used here only
as a disambiguation key for polyphonic characters and is not written to cards.
"""

from __future__ import annotations

import csv
import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
CONVERTER_DIR = PROJECT_DIR / "_sources" / "putonghua-ipa-converter"
CONVERTER_DATA_DIR = CONVERTER_DIR / "data"
CONVERTER_IPA_CSV_URL = (
    "https://raw.githubusercontent.com/nk2028/putonghua-ipa-converter/main/data/ipa.csv"
)

# Same numeric value as the website's default option: UntPhesoca 宽.
SCHEME_INDEX = 1

TONES_TO_IPA = [
    ",,,,,,,,,,".split(","),
    "˥,˥,˥,˥,˥,˥,˥,˥,˥,˥,˥".split(","),
    "˧˦,˧˥,˧˥,˧˥,˧˥,˧˥,˧˥,˧˥,˧˥,˧˥,˧˥".split(","),
    "˨˩,˨˩˦,˨˩˦,˨˩˧,˨˩˧,˨˩˦,˨˩˦,˨˩˦,˨˩˦,˨˩˦,˨˩˦".split(","),
    "˥˧,˥˩,˥˩,˥˩,˥˩,˥˩,˥˩,˥˩,˥˩,˥˩,˥˩".split(","),
]


@dataclass(frozen=True)
class ConvertedExample:
    term: str
    pinyin_numbers: tuple[str, ...]


@dataclass(frozen=True)
class ManualExample:
    display: str


Example = ConvertedExample | ManualExample


INITIAL_EXAMPLES: dict[str, list[Example]] = {
    "x": [ConvertedExample("学习", ("xue2", "xi2"))],
    "f": [ConvertedExample("方法", ("fang1", "fa3"))],
    "g": [ConvertedExample("国家", ("guo2", "jia1"))],
    "k": [ConvertedExample("科学", ("ke1", "xue2"))],
    "l": [ConvertedExample("蓝天", ("lan2", "tian1"))],
    "m-": [ConvertedExample("美妙", ("mei3", "miao4"))],
    "n- / -n": [ConvertedExample("南方", ("nan2", "fang1"))],
    "ni/ü(-)": [ManualExample("年轻 /nʲɛn˧˥ t͡ɕʰiŋ˥/")],
    "-ng": [ConvertedExample("声音", ("sheng1", "yin1"))],
    "b": [ConvertedExample("北京", ("bei3", "jing1"))],
    "p": [ConvertedExample("皮肤", ("pi2", "fu1"))],
    "r-": [ConvertedExample("人民", ("ren2", "min2"))],
    "s": [ConvertedExample("思索", ("si1", "suo3"))],
    "sh": [ConvertedExample("生活", ("sheng1", "huo2"))],
    "d": [ConvertedExample("大地", ("da4", "di4"))],
    "t": [ConvertedExample("天空", ("tian1", "kong1"))],
    "j": [ConvertedExample("经济", ("jing1", "ji4"))],
    "q": [ConvertedExample("清泉", ("qing1", "quan2"))],
    "z": [ConvertedExample("昨天", ("zuo2", "tian1"))],
    "c": [ConvertedExample("从前", ("cong2", "qian2"))],
    "zh": [ManualExample("真正 /ʈ͡ʂən˥ ʈ͡ʂɤŋ˥˩/")],
    "ch": [ManualExample("吃饭 /ʈ͡ʂʰɻ̩˥ fan˥˩/")],
    "h": [ConvertedExample("互相", ("hu4", "xiang1"))],
    "连读“啊”等环境": [ManualExample("撕啊 /sɹ̩˥ zä˨˩/")],
    "零声母/连读环境": [ManualExample("偶尔 /ʔou̯˩˦ ʔäɚ̯˨˩˦/")],
    "-i- / y": [ConvertedExample("牙齿", ("ya2", "chi3"))],
    "c(h)/s(h)/z(h)ir": [ManualExample("事儿 /ʂɉɚ˥˩/")],
    "-u- / w": [ConvertedExample("外文", ("wai4", "wen2"))],
    "j/q/x/yu-, -ü-": [ConvertedExample("月亮", ("yue4", "liang4"))],
    "m": [ManualExample("呣 /m̩˧˥/")],
    "hm": [ManualExample("噷 /m̥˧˩/")],
    "n": [ManualExample("唔 /n̩˧˥/")],
    "ng": [ManualExample("嗯 /ŋ̍˧˥/")],
    "hng": [ManualExample("哼 /ŋ̊˧˩/")],
    "c/s/zi": [ConvertedExample("四次", ("si4", "ci4"))],
    "ch/r/sh/zhi": [ManualExample("日常 /ɻ̩˥˩ ʈ͡ʂʰɑŋ˧˥/")],
}


FINAL_EXAMPLES: dict[str, list[Example]] = {
    "an / ai 环境": [ConvertedExample("安全", ("an1", "quan2"))],
    "a": [ManualExample("大巴 /tä˥˩ pä˥/")],
    "ang / ao 环境": [ConvertedExample("昂贵", ("ang2", "gui4"))],
    "ê / ye / ie": [ManualExample("夜晚 /je̞˥˩ wan˨˩˦/")],
    "en / un": [ConvertedExample("认真", ("ren4", "zhen1"))],
    "-r / 儿化": [ManualExample("鱼儿 /ɥɚ˧˥/")],
    "a/e/ingr 儿化": [ManualExample("风儿 /fɚ̃˥/")],
    "yan / -i": [ManualExample("演员 /jɛn˨˩˦ ɥɛn˧˥/")],
    "i / yi / -in / -ing": [ConvertedExample("意义", ("yi4", "yi4"))],
    "o": [ManualExample("波浪 /po̞˥ lɑŋ˥˩/")],
    "or 儿化": [ManualExample("窝儿 /wo̞˞˥/")],
    "ue(n) / üe(n)": [ManualExample("月亮 /ɥœ̜˥˩ ljɑŋ˥˩/")],
    "u": [ConvertedExample("无人", ("wu2", "ren2"))],
    "ur 儿化": [ManualExample("兔儿 /tʰu˞˥˩/")],
    "ong": [ConvertedExample("工作", ("gong1", "zuo4"))],
    "ongr 儿化": [ManualExample("洞儿 /tʊ̃˞˥˩/")],
    "e": [ConvertedExample("俄语", ("e2", "yu3"))],
    "eng": [ManualExample("仍然 /ɻɤ̞ŋ˧˥ ɻan˧˥/")],
    "er 儿化": [ManualExample("个儿 /kɤ˞˥˩/")],
    "ü / yu(n)": [ConvertedExample("语音", ("yu3", "yin1"))],
    "ai": [ManualExample("爱好 /ʔai̯˥˩ xɑu̯˥˩/")],
    "-r": [ManualExample("二十 /ʔäɚ̯˥˩ ʂɻ̩˧˥/")],
    "angr 儿化": [ManualExample("房儿 /fä̃ɚ̯̃˧˥/")],
    "yanr / -i/-u/-ü 儿化": [ManualExample("烟儿 /jɐɚ̯˥/")],
    "ao": [ManualExample("奥运 /ʔɑu̯˥˩ yn˥˩/")],
    "aor 儿化": [ManualExample("包儿 /pɑu̯˞˥/")],
    "ei / ui": [ManualExample("北方 /pei̯˨˩˦ fɑŋ˥/")],
    "ou / iu": [ManualExample("欧洲 /ʔou̯˥ ʈ͡ʂou̯˥/")],
    "our 儿化": [ManualExample("勾儿 /kou̯˞˥/")],
}


TONE_EXAMPLES: dict[int, list[Example]] = {
    1: [
        ManualExample("天空 /tʰjɛn˥˥ kʰʊŋ˥˥/"),
        ManualExample("书包 /ʂu˥˥ pɑu̯˥˥/"),
    ],
    2: [
        ManualExample("人民 /ɻən˧˥ min˧˥/"),
        ManualExample("学习 /ɕɥɛ˧˥ ɕi˧˥/"),
    ],
    3: [
        ManualExample("可爱 /kʰɤ˨˩˦ ʔai̯˥˩/"),
        ManualExample("语文 /y˨˩˦ wən˧˥/"),
    ],
    4: [
        ManualExample("电话 /tjɛn˥˩ xwa˥˩/"),
        ManualExample("世界 /ʂɻ̩˥˩ t͡ɕjɛ˥˩/"),
    ],
    5: [
        ManualExample("好吗 /xɑu̯˨˩˦ ma/"),
    ],
}


def load_pinyin_to_ipa() -> dict[str, list[str]]:
    path = CONVERTER_DATA_DIR / "ipa.csv"
    if not path.exists():
        CONVERTER_DATA_DIR.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(
            CONVERTER_IPA_CSV_URL,
            headers={"User-Agent": "MandarinIPAAnkiExampleRefresh/0.1"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            path.write_bytes(response.read())
    if not path.exists():
        raise FileNotFoundError(f"缺少转换器数据文件：{path}")
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        next(reader)
        return {row[0]: row[1:] for row in reader if row}


def pinyin_number_to_ipa(pinyin: str, pinyin_to_ipa: dict[str, list[str]]) -> str:
    if not pinyin or not pinyin[-1].isdigit():
        raise ValueError(f"拼音读音必须以数字声调结尾：{pinyin}")
    base = pinyin[:-1]
    tone = int(pinyin[-1])
    if base not in pinyin_to_ipa:
        raise KeyError(f"转换器 ipa.csv 中找不到拼音：{base}")
    ipa_values = pinyin_to_ipa[base]
    try:
        return ipa_values[SCHEME_INDEX] + TONES_TO_IPA[tone][SCHEME_INDEX]
    except IndexError as exc:
        raise IndexError(f"转换器方案索引无效：{SCHEME_INDEX}") from exc


def render_example(example: Example, pinyin_to_ipa: dict[str, list[str]]) -> str:
    if isinstance(example, ManualExample):
        return example.display
    syllables = [pinyin_number_to_ipa(pinyin, pinyin_to_ipa) for pinyin in example.pinyin_numbers]
    if len(example.term) != len(example.pinyin_numbers):
        raise ValueError(f"{example.term} 的字数和读音数量不一致：{example.pinyin_numbers}")
    return f"{example.term} /{' '.join(syllables)}/"


def render_examples(examples: list[Example], pinyin_to_ipa: dict[str, list[str]]) -> str:
    return "、".join(render_example(example, pinyin_to_ipa) for example in examples)


def load_json(filename: str) -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def write_json(filename: str, data: list[dict[str, Any]]) -> None:
    (DATA_DIR / filename).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def update() -> None:
    pinyin_to_ipa = load_pinyin_to_ipa()

    initials = load_json("initials.json")
    for item in initials:
        key = item["pinyin"]
        if key not in INITIAL_EXAMPLES:
            raise KeyError(f"initials.json 缺少例词映射：{key}")
        item["example_word"] = render_examples(INITIAL_EXAMPLES[key], pinyin_to_ipa)
    write_json("initials.json", initials)

    finals = load_json("finals.json")
    for item in finals:
        key = item["final"]
        if key not in FINAL_EXAMPLES:
            raise KeyError(f"finals.json 缺少例词映射：{key}")
        item["example_word"] = render_examples(FINAL_EXAMPLES[key], pinyin_to_ipa)
    write_json("finals.json", finals)

    tones = load_json("tones.json")
    for item in tones:
        tone_number = int(item["tone_number"])
        if tone_number not in TONE_EXAMPLES:
            raise KeyError(f"tones.json 缺少例词映射：{tone_number}")
        item["example_word"] = render_examples(TONE_EXAMPLES[tone_number], pinyin_to_ipa)
    write_json("tones.json", tones)


def main() -> None:
    update()
    print("已更新 data/initials.json、data/finals.json、data/tones.json 的例词 IPA。")
    print(f"转换器数据源：{CONVERTER_DIR}")
    print("卡片例词不会写入拼音。")


if __name__ == "__main__":
    main()
