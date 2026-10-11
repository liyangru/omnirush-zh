# legacy —— 历史分层补丁脚本

**这些脚本在当前 build 上已经跑不通，请不要直接运行。**

它们只作为**译文数据的来源**保留：`gen_dict.py` 用 AST 读取它们里面的译文表
（`TRANS` / `ANCHORS` / `T` / `T3` / `A` / `RAW`），汇总成 `zh_dict.json` 和
`zh_anchors.json`。删掉它们，字典就没法重新生成了。

## 为什么跑不通

最初的汉化是「十层补丁」：每层针对一个界面区域，用**字节偏移量**定位字符串。
应用一自动更新，bundle 文件名和全部偏移量都会变，这些偏移就全失效了
（例如 `patch_hardcoded.py` 会报一堆「锚点缺失 / 不是引号」然后中止）。

现在的方案已经改成**与版本无关**的内容级流水线，见上一级目录的
`apply_all2.py` 与 `apply_dict.py`。

## 各脚本对应哪一层

| 文件 | 原层级 | 覆盖范围 |
|---|---|---|
| `patch_hardcoded.py` | 第 2 层 | 首页问候语、6 张启动卡片、侧栏、命令面板 |
| `patch_hardcoded2.py` | 第 3 层 | 提供商连接、会话输入区、内置浏览器、应用仪表盘、自动化、设置面板 |
| `patch_hardcoded3.py` | 第 4 层 | 浏览器登录状态、共享、诊断说明、UI 控制 MCP 工具名 |
| `patch_settings.py` | 第 5 层 | 设置总览页（卡片数组 / 标签映射 / 分组标题） |
| `patch_final.py` | 第 6 层 | 模型选择器、命令面板条目、扩展卡说明、状态提示 |
| `patch_ext.py` | 第 7 层 | 扩展定义区、计算机操作面板、提供商开关 |
| `patch_ui.py` | 第 8 层 | 全量 UI 文案清扫（JSX 片段、按钮、长说明） |
| `patch_ui2.py` | 第 9 层 | 开发者性能面板、状态映射表、MCP 工具描述 |
| `patch_ui3.py` | 第 10 层 | 提示 / 错误 / 空态全量清扫（527 处） |
| `apply_all.py` | — | 旧的十层编排入口，已被 `apply_all2.py` 取代 |
| `trans2_part2.py` | — | 早期译稿 |
| `scan_hardcoded.py` | — | 只服务第 3 层，产出 `hardcoded_ui.json` |
| `hardcoded_ui.json` | — | 只被第 3 层读取 |

## 注意

- `patch_ui3.py` 的 `T` 表里存的是 **(偏移, 译文)**，其中偏移指向
  `_l9_snapshot.js`（未入库）里的英文原文。`gen_dict.py` 就是靠这个配对
  反推出 471 条译文的英文原文。**没有快照时 `gen_dict.py` 会拒绝写入**，
  以免把已提交的字典覆盖掉。
- 这些脚本里的 `HERE` / `BUNDLE` 仍然指向当前安装目录，但**不要运行**。
