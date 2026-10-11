# OmniRush 汉化补丁

把已安装的 OmniRush 桌面版界面文案替换为简体中文。

## 现状

| 项 | 值 |
|---|---|
| 应用 | OmniRush.ai Desktop（官方安装包） |
| 渲染层位置 | `%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\` |
| 原始 bundle | 5,271,388 字符，中文汉字 12,324 个 |
| 汉化后 | 5,273,775 字符，中文汉字 **38,944** 个（**+215%**） |
| 官方中文覆盖率 | 1168 / 2101 键 |
| 补全后 | **2078 键 = 100% 功能覆盖** |
| 界面文案 | 内容级字典 **1360 条**，共替换 **1457+ 处** |
| 应用可执行性 | 模块求值成功；`OmniRush.ai.exe --version` → `v24.18.0`（正常） |

> 渲染层 UI 不在 `app.asar` 里，而是 electron-builder 的 extraResources，
> 所以汉化只需替换 `resources/app-dist/` 下的 bundle，**无需解包/重打包 asar**。

## 一键重新应用（推荐）

```bash
python apply_all2.py
```

幂等：每次先从 `.orig-backup` 还原官方原版，再打补丁，最后跑四道校验。

## ⚠️ 应用会自动更新，补丁会被覆盖

**应用升级会重写整个 `app-dist/`**，bundle 文件名带内容 hash
（`app-CAtSUbH6.js` → `app-DohXHoBv.js`），全部偏移量和备份一起作废。
所以整套工具已经改成**与文件名/偏移无关**：

- `_bundle.py` 从 `index.html` 的 `<script src>` 反查当前真实 bundle 名，
  所有脚本共用，**换版本不用改代码**；
- 译文全是「内容级」的（英文原文 → 中文），不依赖偏移；
- `apply_all2.py` 是幂等入口，升级后直接重跑即可。

如果更新后 `apply_all2.py` 报「找不到 app-\*.js 入口引用」，说明目录结构又变了，
改 `_bundle.py` 里的正则即可。

## 译文数据

| 文件 | 内容 |
|---|---|
| `zh.ts`（`../omnirush-i18n/`） | 补全版中文语言包，2078 键，i18n 层专用 |
| `zh_dict.json` | 平铺字典：英文原文 → 中文，1004 条 |
| `zh_anchors.json` | 复合锚点（整段代码片段替换，语境更精确），106 条 |
| `zh_extra.json` | 补充字典：新版新增文案，178 条 |

`gen_dict.py` 用 AST 从各历史补丁脚本里抽取译文、从 `_l9_snapshot.js` 反推
第十层的英文原文，生成上面两个文件；改完历史脚本后重跑它即可刷新。
`zh_extra.json` 是手写的（新版新增界面文案）。

## 流程（apply_all2.py）

| 步骤 | 脚本 | 内容 |
|---|---|---|
| 1 | `patch_zh.py` | 注入补全版 zh 语言包、清空 `ENGINE_DETAIL_KEYS`、默认语言改 zh；覆盖率对照**当前 bundle 的 en 对象**，不足即中止 |
| 2 | `apply_dict.py` | 先套复合锚点，再按**英文长度从长到短**套平铺字典；`.mjs` 强制 ESM 语法校验 |
| 3 | `verify_*.py` | 四道校验 |

`apply_dict.py` 的两个关键设计：

- **长句优先**：否则短句先替换会把长句打碎（例如 `"Same as main agent"`
  必须晚于包含它的整句）。
- **模板字面量兜底**（`apply_template`）：压缩产物里的 `${...}` 是变量名/表达式，
  换版本就变（`${Dt}` → `${xJe}`）。兜底逻辑用**文案文本段**在新 bundle 里
  定位同名模板，再把旧占位符映射成新的。这解决了 15 条含插值的文案。

## 校验脚本

| 脚本 | 作用 |
|---|---|
| `verify_syntax.py` | **最可靠的一道防线**：`.mjs` 强制按 ES Module 解析 |
| `verify_final.py` | Node 取出 bundle 运行时真实字符串，与期望值逐键比对 |
| `verify_hardcoded.py` | 首页/侧栏英文是否清零、中文是否就位 |
| `verify_settings.py` | 设置总览页（标签映射 / 描述映射 / 分组标题） |
| `check_comparisons.py` | 在原版中找出「被 `===` / `!==` 比较的英文长句」，排查误译导致逻辑失效 |
| `modprobe.mjs` | Node + 最小 DOM 桩 import bundle，验证模块求值不抛异常 |
| `list_targets.py` | 排除第三方库区域后列出剩余应用文案（完整文本） |
| `scan_ui.py` / `scan_sentences.py` / `scan_sweep.py` | 三种口径的英文扫描 |
| `_bundle.py` | 打印当前检测到的 bundle 路径 |

## 性能

全流程 `apply_all2.py` 约 **18 秒**（补丁部分约 9 秒）。

早期版本每命中一条字典就要重建整个 5.3 MB bundle 字符串
（约 1175 次、每次搬 10 MB），光这一项就要 12 秒。
现在改为**找齐所有命中位置 → 去重叠 → 一次写回**：

- 条目按英文长度降序处理，去重叠时「同起点保留更长者」，
  正好等价于原来的「长句优先」语义；
- i18n 数据区边界只定位一次，之后按替换长度差增量平移；
- 验证方式：与逐条替换版**逐字节比对**（sha256 一致）才算通过。

## 已修复事故

### 一、白屏（双反引号 + node --check 假阳性）

1. **双反引号**：译文字面量自带反引号，脚本又包一层 → `` ``译文`` ``，
   整个模块解析失败。修复：反引号定界符时先剥掉译文自带的一层。
2. **`node --check <file>.js` 在这份 bundle 上会静默返回 0**（ESM 检测只看
   文件开头，`export` 在末尾）。修复：一律用 `.mjs` 后缀强制 ESM 解析。
3. **校验手段本身要验证**：已补反向测试（故意注入已知错误必须报错）。

### 二、应用自动更新清空补丁

某次重启后应用自动升级，`app-dist/` 被重写，补丁全丢。修复：见上一节，
整套工具改为内容级 + 自动探测 bundle 名。

## 补丁原理 / 踩坑记录

- 渲染层 bundle 是 esbuild 压缩产物，含 `\n` 的字符串会写成反引号模板字面量；
  还可能是 `"…"`、`'…'` 或 `` `…` ``，必须实测定界符。
- 反引号模板支持 `${}` 嵌套与内层模板（如 `` `a${c?`b${x}`:""}` ``），
  普通正则会从内层反引号处截断，需要带 `${}` 深度计数的提取器。
- **同一文案会出现多次，必须全量替换**（`list_targets.py` 去重只留首次，
  害过两次）。反例：`"Control mode is off."` 在原版里同时用于 state 初值、
  `f==="..."` 比较和 else 赋值，三处必须同步替换。
- i18n 数据区（`"account.mcp_connected_one"` 起到 `;function Ws(`）全程排除，
  官方十种语言包一字未动；`patch_zh.py` 只替换其中 zh 那一个对象。
- 新版把设置总览重构成两个 `switch` 函数，硬编码文案**不带句末句号**；
  旧锚点带句号，所以失效。字典里带句号与不带句号两种形式都要收。
- 含反引号的文案也可能是双引号字符串（例如 `` Entries include `pinned` ``），
  所以定界符要三种都试，不能因为含反引号就只试反引号。

## 回滚

```bash
B=$(python -c "import sys;sys.path.insert(0,'.');from _bundle import detect_bundle;print(detect_bundle())")
cp "$B.orig-backup" "$B"
```

`.orig-backup` 即官方原版，未做任何改动。

## 仍未汉化（有意保留）

- **第三方库内部报错**：React Router、Zod、KaTeX、Mermaid、shiki、xterm、
  MCP SDK、react-resizable-panels 等，仅开发者在控制台可见。
- **面向大模型的提示词**：如「Resolve "today", "tomorrow"…」。
- **产品名与列表**：`omnirush.ai Cloud`、`Google Workspace`、语法高亮语言名，
  以及 `ChatGPT、Claude、Gemini…` 这类已含中文标点的产品列表。
- CSS `className`、组件 `displayName`、文件路径、存储键名、键盘快捷键。

## 目录说明

- 根目录：活跃工具链（`apply_all2.py` 主链路 + 校验 + 扫描）
- `legacy/`：历史分层补丁脚本。**在当前 build 上已跑不通**，
  只作为 `gen_dict.py` 的译文表来源保留，详见 `legacy/README.md`

## 未入库的文件（可重新生成）

以下文件**没有**随仓库分发， 主链路也不需要它们；
只有不在主链路里的历史脚本（`patch_hardcoded*.py` / `patch_final.py` /
`patch_ui3.py` / `gen_dict.py` 的反推步骤）才会用到：

| 文件 | 用途 | 怎么重新生成 |
|---|---|---|
| `_l9_snapshot.js` | 某次构建的 bundle 副本，用于反推第 10 层的英文原文 | 打完前九层后 `cp <bundle> _l9_snapshot.js` |
| `remaining_en.json` | 英文扫描结果 | `python scan_remaining.py` |
| `remaining2.json` | 区域扫描结果 | `python scan_region.py <lo> <hi>` |
| `hardcoded_ui.json` | 硬编码文案清单 | `python scan_hardcoded.py`（已入库，此处仅备注） |

缺失时 `gen_dict.py` 会打印说明并**一个文件都不写**，以免覆盖已提交的
`zh_dict.json`（里面 471 条译文就是从快照反推来的）。

另：官方安装包、bundle 副本、`reference/` 里的官方源码都未入库——
体积大且属应用专有内容，详见根目录 `.gitignore`。

## 注意

- **打完补丁必须重启应用**。如果是在应用运行期间覆盖 bundle，
  旧进程仍持有旧代码，可能表现为白屏或界面不动。
- 自动更新会再次清掉补丁，升级后重跑 `python apply_all2.py`。
