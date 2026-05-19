# 普通话 IPA Anki 卡组

面向中文母语者的普通话 IPA / 语音学入门 Anki 卡组制作项目。

这个卡组假设学习者已经会说普通话。它不是儿童拼音教材，也不是外国人普通话发音入门；目标是帮助中文母语者读懂普通话 IPA、理解基本语音学概念，并能把 IPA 符号和普通话拼音环境对应起来。

Anki 卡组名：

```text
IPA · 普通话
```

卡组文件：

```text
output/Chinese_IPA_Mandarin.apkg
```

## 下载

普通用户可以直接从 GitHub Releases 下载 `.apkg` 文件，然后导入 Anki。

开发者或想自行修改数据的人，可以克隆本仓库后重新构建卡组。

## 学习目标

卡组重点训练：

- 看到 IPA，识别它在普通话中对应的拼音或拼音环境。
- 读懂辅音、半元音、音节辅音、元音、双元音、儿化和声调相关符号。
- 理解送气/不送气、塞音/塞擦音/擦音、卷舌/龈腭、音节辅音、轻声、第三声变调等概念。
- 了解普通话 IPA 中常见的宽式/窄式和资料差异。

卡片正面保持极简，只显示 IPA 或概念本身。音频只出现在背面，不在正面显示或自动播放。

## 子卡组

```text
IPA · 普通话::01 IPA 识别::01 辅音
IPA · 普通话::01 IPA 识别::02 半元音与音节辅音
IPA · 普通话::01 IPA 识别::03 元音
IPA · 普通话::01 IPA 识别::04 双元音与儿化
IPA · 普通话::01 IPA 识别::05 声调
IPA · 普通话::02 语音学概念::01 读表基础
IPA · 普通话::02 语音学概念::02 音段类型
IPA · 普通话::02 语音学概念::03 普通话重点
```

当前版本不提供 `拼音 -> IPA` 方向的卡，也不单独提供 IPA 对比子卡组。训练方向以 `IPA -> 拼音/音值理解` 和语音学概念为主。

## 导入 Anki

1. 下载 `Chinese_IPA_Mandarin.apkg`。
2. 打开 Anki。
3. 选择“文件 / 导入”。
4. 选择下载的 `.apkg` 文件并确认导入。

## 本地构建

安装依赖：

```bash
pip install -r requirements.txt
```

如果系统需要显式使用 Python 3：

```bash
python3 -m pip install -r requirements.txt
```

推荐使用虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

构建卡组：

```bash
python build_deck.py
```

或：

```bash
python3 build_deck.py
```

构建成功后，终端会输出 note 数量、card 数量、输出路径和媒体文件数量。

## 项目结构

```text
mandarin-ipa-anki/
  README.md
  requirements.txt
  build_deck.py
  data/
    initials.json
    finals.json
    tones.json
    contrasts.json
    concepts.json
  media/
    README.md
    audio_manifest.csv
    *.mp3
  output/
    Chinese_IPA_Mandarin.apkg
    audio_attribution.csv
  scripts/
    fetch_ipa_audio.py
    update_example_ipa_from_converter.py
    import_private_anki_audio.py
```

`data/contrasts.json` 目前作为参考素材保留，默认不制作对比卡。

## 数据与更新

数据和构建逻辑分离：

- `data/initials.json`：辅音、半元音、音节辅音。
- `data/finals.json`：元音、双元音、儿化音。
- `data/tones.json`：声调。
- `data/concepts.json`：语音学概念。
- `data/contrasts.json`：音系对比参考素材。

修改 JSON 后重新运行：

```bash
python build_deck.py
```

`build_deck.py` 会检查必需字段、空字段和例词格式。声母、韵母、声调卡的 `example_word` 应写成“词语 /IPA/”，不应写拼音。

批量刷新例词 IPA：

```bash
python scripts/update_example_ipa_from_converter.py
python build_deck.py
```

该脚本使用 `nk2028/putonghua-ipa-converter` 的开源数据转换大部分例词 IPA，并对少数需要贴合本卡组符号体系的项目保留人工校订例词。拼音只作为脚本内部的多音字消歧信息，不写入卡片。

## 稳定更新

本项目固定配置 Deck ID 和 Model ID，并为每张 note 使用稳定 GUID。更新数据后重新构建并导入 Anki 时，已有复习记录会尽量保留。

## 音频

当前卡组包含背面音频：

- 优先使用可直接对应 IPA 符号的公开 IPA 音频。
- 缺少合适 IPA 单音时，使用普通话音节示范音频作为辅助。
- 所有媒体统一为 MP3，兼容 AnkiMobile/iPhone。
- 正面模板不包含 `Audio` 字段。

音频来源记录：

- `media/audio_manifest.csv`
- `output/audio_attribution.csv`

重新抓取音频时，先准备 `_sources/` 中所需的上游页面或压缩包，再运行：

```bash
.venv/bin/python scripts/fetch_ipa_audio.py --clear-media --overwrite --delay 25
```

脚本对在线音频下载使用单线程和 25 秒间隔。

## IPA 写法说明

普通话 IPA 存在宽式/窄式、学派、教材和资料差异。本卡组以学习理解为目标，不把某一种写法说成唯一绝对答案。

当前数据保留了一些比常见入门写法更细的符号，例如：

- `r` 可见 `[ɻ]`、`[ʐ]` 等分析。
- `zh/ch` 可写作 `[ʈ͡ʂ]`、`[ʈ͡ʂʰ]`，有些资料会写 `[t͡ʂ]`、`[t͡ʂʰ]`。
- `zi/ci/si` 后面的音可写作 `[ɹ̩]`，有些资料会写 `[ɿ]`。
- `zhi/chi/shi/ri` 后面的音可写作 `[ɻ̩]`，有些资料会写 `[ʅ]`。
- `a/e/o/ong/eng/ian` 等韵母有较细的环境变体。

卡片中的“易混点”是学习提示，不是语料统计结论。

## 来源与署名

- 例词 IPA 参考 `nk2028/putonghua-ipa-converter`，该项目使用 CC0-1.0。
- 音频来自多个公开来源，具体来源、作者和许可信息见 `media/audio_manifest.csv`。
- Release 附带 `audio_attribution.csv`，便于随卡组保留音频来源信息。

第三方音频不适用单一仓库许可；重新分发或改编时应检查对应源文件页面和清单中的许可说明。
