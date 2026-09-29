# 红魔 Duo 状态栏素材库

为 [红魔 Duo](https://github.com/liligit1815/LS_Augment) 提供可本地导入的状态栏图标、动画与字体包。素材使用和投稿互相独立：下载不要求 GitHub 登录，个人导入的文件不会自动上传。

## 下载与使用

1. 在下方目录选择素材，或进入 [最新素材发布](https://github.com/liligit1815/RedMagicDuo-Assets/releases/latest)。
2. 下载带 `.zip` 后缀的素材附件。GitHub 自动生成的 Source code ZIP 是仓库源码，不能作为素材包导入。
3. 在红魔 Duo 的“状态栏 → 图标与字体素材”选择“导入素材包”。查看名称、作者、许可和素材数量，载入预览后点击“应用”。
4. 导入仅覆盖包内涉及图标的素材映射和明确指定的字体角色，保留其他素材及图标显隐、位置、行数和布局。包内没有覆盖的图标状态保留原厂显示。

| 素材 | 内容 | 许可 | 预览 |
| --- | --- | --- | --- |
| [Mono Essentials](https://github.com/liligit1815/RedMagicDuo-Assets/releases/download/v1.0.0/mono-essentials-1.0.0.zip) | 程序绘制的原创单色状态图标 | MIT | [预览](previews/mono-essentials.png) |
| [Gentle Spin](https://github.com/liligit1815/RedMagicDuo-Assets/releases/download/v1.0.0/gentle-spin-1.0.0.zip) | 原创低帧率风扇动画 | MIT | [预览](previews/gentle-spin.webp) |
| [Noto Sans](https://github.com/liligit1815/RedMagicDuo-Assets/releases/download/v1.0.0/noto-sans-1.0.0.zip) | Noto Sans 字体，适合时间、数字、拉丁文字 | SIL OFL 1.1 | [字体来源](https://github.com/google/fonts/tree/main/ofl/notosans) |

Noto Sans 此文件不包含中文字符；混排中文交给系统字体回退。素材格式版本为 1，需使用支持状态栏素材功能的红魔 Duo 版本。三个示例包可依次载入组成一套外观；导入 Noto Sans 不会清空已选图标。已存在的同名图标会整体替换其状态与层映射，建议修改前导出当前素材组合。

## 投稿

在应用中选择“导出分享包”，填写名称、作者、许可，确认仅包含自己允许分享的素材后导出。然后打开 [素材投稿表单](https://github.com/liligit1815/RedMagicDuo-Assets/issues/new?template=asset-submission.yml)，上传 ZIP 并提供预览和来源。**提交 Issue 不会立即上架**，维护者校验并审核后发布。

熟悉 GitHub 的作者也可以通过 PR 提交目录元数据、预览、授权说明及 ZIP 下载位置。不要提交完整设备备份、日志、账号信息、原厂字体或来源不明的图片。详见 [投稿指南](CONTRIBUTING.md)。

## 维护与格式

- `catalog.json`：应用可读取的素材目录，记录版本、下载地址、SHA-256、包大小及许可。
- `previews/`、`licenses/`：预览和授权原文。
- `tools/build_examples.py`：生成原创图标、动画与示例包；字体来自固定上游提交。
- `tools/validate_pack.py`：校验 ZIP 路径、解压大小、白名单、哈希、真实图片解码和字体结构。
- [FORMAT.md](FORMAT.md)：格式、边界与兼容规则。

素材 ZIP 通过 Releases 分发，避免频繁二进制更新扩大 Git 历史。未经审核的附件不进入 `catalog.json`。维护者发布新版使用新版本和新附件名，保留旧包供回退。
