# media/

本目录保存会被打包进 Anki 卡组的 MP3 音频。`build_deck.py` 中的 `INCLUDE_AUDIO = True`，但卡片正面模板不包含 `Audio` 字段，音频只出现在背面。

音频来源策略：

1. 优先使用可直接对应 IPA 符号的公开 IPA 音频。
2. 没有合适 IPA 单音时，使用普通话音节示范音频作为辅助。
3. 辅助音频不是孤立 IPA 单音，卡背会标明“示范音节”。
4. 每个 MP3 都必须在 `audio_manifest.csv` 中登记来源、作者和许可信息。

`audio_manifest.csv` 字段：

```text
filename,source_project,source_title,source_url,author,license,license_url,notes
```

重新抓取音频：

```bash
.venv/bin/python scripts/fetch_ipa_audio.py --clear-media --overwrite --delay 25
```

这个脚本对在线音频下载使用单线程和 25 秒间隔。普通话音节示范音频从本地 `_sources/` zip 文件读取。
