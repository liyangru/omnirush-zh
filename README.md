# OmniRush 简体中文汉化

[![CI](https://github.com/liyangru/omnirush-zh/actions/workflows/ci.yml/badge.svg)](https://github.com/liyangru/omnirush-zh/actions/workflows/ci.yml)

把 **OmniRush.ai 桌面版**的界面文案完整本地化为简体中文。

OmniRush 官方只内置了 **55.6%** 的中文（1168 / 2101 个 i18n 键），
而且有大量文案是**硬编码在源码里、根本没接 i18n** 的——这些无论选什么语言都显示英文。
本项目把它补到了 **100%**。

> 这是第三方本地化项目，与 OmniRush 官方无关。
> 只操作你本机已安装的应用，不需要重新打包安装包。

## 效果

| 项 | 值 |
|---|---|
| 中文汉字数 | 12,324 → **38,956**（**+216%**） |
| i18n 语言包 | 1168 → **2078 键，100% 功能覆盖** |
| 界面硬编码文案 | 内容级字典 **1360+ 条**，替换 **1,350+ 处** |
| 校验 | 语法 / 键值 / 残留英文 / 模块求值 四项全绿 |

## 用法

```bash
# 1. 先装好 OmniRush 桌面版
# 2. 一键汉化（幂等：每次先从官方原版还原再打补丁）
cd omnirush-install
python apply_all2.py

# 3. 重启 OmniRush
```

自检（18 项）：

```bash
cd omnirush-install
python preflight.py        # 本机全量：会实际重打一遍补丁并校验
python preflight.py --ci   # 只跑不依赖本机安装的部分（CI 用）
```

## 目录

```
omnirush-i18n/    补全版中文语言包
  zh.ts            2078 键的简体中文翻译（主交付物）
  en.ts            官方英文语言包（从本地 bundle 抽取）
  zh.original.ts   官方原版中文（用于 diff 与核对）
  merge.py         合并多个译稿生成 zh.ts
  trans1-4.json    分批译稿

omnirush-install/ 补丁工具链（与版本无关）
  apply_all2.py    ★ 一键入口：还原 → 打补丁 → 四道校验
  _bundle.py       从 index.html 反查当前 bundle 名（升级后不用改代码）
  patch_zh.py      注入 zh.ts + 清空白名单 + 默认中文
  apply_dict.py    套用内容级译文（锚点 + 平铺字典 + 模板兜底）
  zh_dict.json     平铺字典：英文原文 → 中文（1004 条）
  zh_anchors.json  复合锚点（整段代码片段替换，语境更精确，106 条）
  zh_extra.json    补充字典（新版新增文案，179 条）
  gen_dict.py      用 AST 从 legacy/ 的补丁脚本重新生成字典
  verify_syntax.py ES Module 语法校验（.mjs）
  verify_final.py  运行时字符串逐键比对
  verify_hardcoded.py / verify_settings.py  界面残留检查
  check_comparisons.py  排查「被 === 比较的英文」被误译
  modprobe.mjs     Node 里 import bundle，验证模块求值不抛异常
  list_targets.py  排除库区域后列出剩余应用文案
  scan_ui.py / scan_sentences.py / scan_sweep.py  三种口径英文扫描
  preflight.py     自检（18 项；--ci 跳过需本机安装的部分）
  legacy/          历史分层补丁脚本（已跑不通，只作 gen_dict.py 的数据来源）
  README.md        完整技术文档与踩坑记录
```

## 重要：应用会自动更新，补丁会被覆盖

OmniRush 升级会重写整个 `app-dist/`，bundle 文件名带内容 hash，
全部偏移量和备份一起作废。所以整套工具**不依赖文件名和偏移**：

- `_bundle.py` 从 `index.html` 反查真实 bundle 名；
- 译文全是「内容级」的（英文原文 → 中文）；
- 升级后直接重跑 `python apply_all2.py` 即可。

## 未汉化的部分（有意保留）

- **第三方库内部报错**：React Router、Zod、KaTeX、Mermaid、shiki、xterm、
  MCP SDK 等，仅开发者在控制台可见。
- **面向大模型的提示词**：注入 LLM 的系统指令。
- **产品名与专有名词**：`omnirush.ai Cloud`、`Google Workspace`、
  语法高亮语言名、以及 `ChatGPT、Claude、Gemini…` 这类产品列表。
- CSS 类名、组件 `displayName`、文件路径、存储键名、键盘快捷键。

## 性能

`apply_all2.py` 全流程（打补丁 + 四道校验）约 **18 秒**，其中补丁部分约 9 秒。
关键优化：字面量替换从「每命中一条就重建整个 5.3 MB 字符串」改成
「找齐所有位置 → 去重叠 → 一次写回」，光这一项就从 27 秒降到 11 秒
（输出逐字节一致）。详见 `omnirush-install/README.md`。

## 已知坑（详见 `omnirush-install/README.md`）

1. **`node --check xxx.js` 在这份 bundle 上会静默返回 0** —— ESM 语法检测只看
   文件开头，而 `export` 在末尾。必须用 `.mjs` 后缀强制按 ES Module 解析。
2. **正则扫 JS 源码不可靠** —— 不平衡的反引号会让正则吞噬上千字符，把正常
   字面量整段漏掉。要用带 `${}` 深度计数的提取器。
3. **同一文案会出现多次，必须全量替换** —— 有的字符串同时用于 state 初值、
   `===` 比较和 else 赋值，只改一处会破坏逻辑。
4. **译文字面量若自带定界符，脚本不能再包一层** —— 否则产出双反引号，
   整个模块解析失败、界面白屏。

## 免责声明

本项目是第三方本地化，与 OmniRush 官方无从属关系。
汉化仅在你本机安装的应用上进行；升级会清除补丁，重跑即可。
`omnirush-i18n/zh.ts` 等译文来自对应用内置英文语言包的人工翻译。
