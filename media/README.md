# media/

当前卡组会打包本目录中的 MP3 音频。`build_deck.py` 中的 `INCLUDE_AUDIO = True`，但卡片正面模板不包含 `Audio` 字段，音频只出现在背面。

音频来源策略：

1. 优先使用公开 IPA 音频资料中能直接对应的 IPA 单音。
2. 没有合适单音时，使用 `zispace/hanyu-pinyin-audio` v0.1 release 中的拼音音节示范音频。
3. fallback 音频不是孤立 IPA 单音，卡背会标明“示范音节”。
4. 每个 MP3 都必须在 `audio_manifest.csv` 中登记来源。

`audio_manifest.csv` 字段：

```text
filename,source_project,source_title,source_url,author,license,license_url,notes
```

重新导入音频：

```bash
.venv/bin/python scripts/fetch_ipa_audio.py --clear-media --overwrite --delay 25
```

这个脚本对在线音频下载使用单线程和 25 秒间隔。zispace fallback 从本地 `_sources/` zip 文件读取。
