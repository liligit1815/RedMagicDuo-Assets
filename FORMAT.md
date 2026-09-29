# StatusBarAssets v1

ZIP 只包含 `manifest.json` 和清单列出的 `images/`、`fonts/` 文件。不得包含目录占位条目、符号链接、绝对路径、`..`、反斜线、重复文件、脚本或全量 settings。

```json
{
  "format": "RedMagicDuo.StatusBarAssets",
  "version": 1,
  "metadata": {"name":"Example","author":"Author","license":"MIT","licenseText":"完整许可原文"},
  "theme": "",
  "fonts": "",
  "images": {},
  "fontFiles": {}
}
```

`metadata` 只允许 `name`、`author`、`license`、可选 `licenseText`、`source`、`description`。前三项必填；名称/作者最长 100 字符、许可名 200 字符、许可原文 65536 字符、其他文本 2048 字符。

`theme` 是应用 `StatusBarThemeSpec` 的规范化字符串：空字符串表示原厂素材；非空以 `1;` 开始，各条由分号分隔：`id,state,layer,sha256,originalColor,scale,offsetX,offsetY,opacity,mirror`。数值必须在应用允许的范围内；ID、状态和层由应用兼容目录限定。请在应用导出时生成，避免手动拼接。

`fonts` 是应用 `StatusBarFontSpec` 的规范化字符串：空字符串表示默认；非空如 `1;global=font:<sha256>`，支持角色 `global,clock,network,metrics,battery,bluetooth,other`，值为 `inherit`、`original` 或 `font:<sha256>`。角色按上述顺序序列化。

`images` / `fontFiles` 是 SHA-256 到 ZIP 路径的映射。图像路径必须为 `images/<sha256>.png|jpg|jpeg|gif|webp`；字体路径为 `fonts/<sha256>.ttf|otf|ttc|font`。扩展名不能替代真实解码，哈希必须对应完整文件。主题引用的图像和字体引用的字体必须恰好与清单一致，不能缺失或夹带无引用文件。

资源最大 512 个 ZIP 条目，压缩包 20 MiB、解压合计 64 MiB，清单 256 KiB。字体单个 4 MiB，图片单个 8 MiB；静态图原始边长不超过 4096，动画不超过 1024，实际渲染会缩小到状态栏需要的分辨率。社区校验还限制动画最多 240 帧。实际应用遇到设备不支持的图标或状态时保留原厂对应内容。

预检不保存资源；确认后先保存全部校验过的资源，成功后一次性更新图标主题和字体两个配置项。包不能改变显隐、布局、其他模块功能或运行代码。动画仅在状态栏可见、设备交互且非省电状态时播放。
