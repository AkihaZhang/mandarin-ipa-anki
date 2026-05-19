# 给中文母语者用的普通话 IPA / 语音学入门 Anki 卡组

这个项目用 Python + genanki 生成一个 Anki 卡组：

`output/Chinese_IPA_Mandarin.apkg`

核心使用者是已经会说普通话的中文母语者。它不是“小朋友学拼音”，也不是“外国人学中文发音”，而是帮助中文母语者读懂普通话 IPA 和基础语音学概念。

当前数据围绕现代标准汉语 IPA 的常见标音方式整理，目标是让中文母语者能直接读懂音标、拼音环境和基础语音学概念。

导入 Anki 后，根卡组名是：

```text
IPA · 普通话
```

子卡组结构：

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

## 学习目标

你会重点练习：

- 看到 IPA，知道它对应普通话哪个拼音或拼音环境。
- 能读懂辅音、半元音、音节辅音、元音、双元音、儿化和声调表。
- 理解送气/不送气、塞音/塞擦音/擦音、卷舌/龈腭、音节辅音、轻声、第三声变调等概念。

卡组不生成 `拼音 -> IPA` 方向的卡，也不再单独生成 IPA 对比子牌组。训练方向以 `IPA -> 拼音/音值理解` 和语音学概念为主，避免把学习变成普通拼音复习或重复对比题。

所有卡片正面都尽量极简：只显示 IPA 或概念本身。音频只出现在背面，不在正面自动播放或显示。

卡片会自动带难度标签：

- `level:1`：基础音系框架和最常见对立。
- `level:2`：普通话重点难点，如卷舌、龈腭、音节辅音和元音环境变体。
- `level:3`：细节项，如儿化、拼音省写、轻声和变调。

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
    contrasts.json   # 参考数据；默认不生成对比卡
    concepts.json
  media/
    README.md
    audio_manifest.csv
  scripts/
    fetch_ipa_audio.py
    update_example_ipa_from_converter.py
    import_private_anki_audio.py
  output/
```

## 安装依赖

```bash
pip install -r requirements.txt
```

如果你的系统没有 `python` / `pip` 命令，但有 Python 3，可以用：

```bash
python3 -m pip install -r requirements.txt
```

macOS Homebrew Python 如果提示 externally-managed-environment，可以用项目内虚拟环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## 生成卡组

在项目根目录运行：

```bash
python build_deck.py
```

如果你的系统需要显式使用 Python 3：

```bash
python3 build_deck.py
```

生成成功后，终端会输出：

- note 数量
- card 数量
- 输出路径
- media 文件数量

卡组文件会写入：

```text
output/Chinese_IPA_Mandarin.apkg
```

## 导入 Anki

1. 打开 Anki。
2. 选择“文件 / 导入”。
3. 选择 `output/Chinese_IPA_Mandarin.apkg`。
4. 确认导入。

本项目固定写死了各子卡组的 Deck ID 和 Model ID，并为每张 note 使用稳定 GUID。以后修改数据后重新生成并导入，Anki 会尽量保留已有复习记录，而不是把所有卡都当成全新卡。

## 音频

当前版本已加入背面音频：

- 优先使用公开 IPA 音频资料中能直接对应的 IPA 单音。
- 没有合适单音的项目，使用 `zispace/hanyu-pinyin-audio` v0.1 release 中的拼音音节示范音频补充。
- 所有媒体统一为 MP3，避免 AnkiMobile/iPhone 端播放问题。
- 正面模板不包含 `Audio` 字段，音频只在背面显示。
- `media/audio_manifest.csv` 和 `output/audio_attribution.csv` 记录音频来源。

重新抓取音频时，先确保 `_sources/` 中已有 IPA 音频页面 HTML 和 `zispace-hanyu-pinyin-audio` v0.1 release zip。然后运行：

```bash
.venv/bin/python scripts/fetch_ipa_audio.py --clear-media --overwrite --delay 25
```

脚本对在线音频下载单线程执行，并在每个下载前等待 25 秒。zispace fallback 从本地 zip 解包，不访问网络。

## 修改数据并重新生成

数据和生成逻辑是分离的：

- 辅音、半元音、音节辅音：`data/initials.json`
- 元音、双元音、儿化音：`data/finals.json`
- 声调：`data/tones.json`
- 音系对比参考数据：`data/contrasts.json`（默认不生成卡）
- 概念：`data/concepts.json`

修改 JSON 后重新运行：

```bash
python build_deck.py
```

脚本会检查必需字段。如果某条数据缺字段或字段为空，会给出清晰错误，方便定位。

声母、韵母、声调卡的例词字段应写成“词语 /IPA/”，不要写拼音。需要批量刷新例词 IPA 时可以运行：

```bash
python scripts/update_example_ipa_from_converter.py
python build_deck.py
```

该脚本使用 `nk2028/putonghua-ipa-converter` 的开源数据生成大部分例词 IPA，并对少数需要贴合本卡组符号体系的项目保留人工校订例词。拼音只作为脚本内部的多音字消歧信息，不写入卡片。`build_deck.py` 也会检查 `example_word`，发现例词里混入拼音会直接报错。

`contrasts.json` 目前只作为参考素材保留，方便以后挑选少量真正必要的对比重新加入。

## 关于 IPA 写法

普通话 IPA 存在宽式/窄式、学派、教材和资料差异。本卡组保留一些比常见入门写法更细的符号。例如：

- `r` 可见 `[ɻ]`、`[ʐ]` 等分析。
- `zh/ch` 可写作 `[ʈ͡ʂ]`、`[ʈ͡ʂʰ]`，有些资料会写 `[t͡ʂ]`、`[t͡ʂʰ]`。
- `zi/ci/si` 后面的音可写作 `[ɹ̩]`，有些资料会写 `[ɿ]`。
- `zhi/chi/shi/ri` 后面的音可写作 `[ɻ̩]`，有些资料会写 `[ʅ]`。
- `a/e/o/ong/eng/ian` 等韵母有较细的环境变体。

本卡组以读懂普通话 IPA 为目标，不把某一种写法说成唯一绝对答案。若公开发布本项目，请保留音频、例词 IPA 和参考资料来源说明。
