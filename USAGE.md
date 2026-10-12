# 使用教程

面向「只想把 OmniRush 界面变成中文」的使用者。全部命令在 **Windows** 上执行。

> 只想快速上手？看 [三步汉化](#二三步汉化)。出问题了看 [常见问题](#五常见问题)。

---

## 一、前置条件

| 需要 | 说明 |
|---|---|
| **Windows** | 补丁脚本按 Windows 路径编写（`%LOCALAPPDATA%`）。macOS / Linux 见[其他平台](#八其他平台) |
| **OmniRush 桌面版** | 已安装并能正常打开。默认装在 `%LOCALAPPDATA%\Programs\@omnirushdesktop\` |
| **Python 3.8+** | 用于运行补丁脚本。装的时候勾上「Add Python to PATH」 |
| **Node.js** | **必需**。补丁写入前用 `node --check` 做语法校验，没有它补丁不会写入 |

### 检查环境

不用自己逐项确认，跑一次环境自检就行：

```bash
cd omnirush-install
python doctor.py
```

输出示例（节选）：

```
[1] 运行平台
  ✅ Windows  — 10.0 build 26200

[2] Python
  ✅ Python 3.13.14

[3] Node.js（语法校验要用）
  ✅ node 可用  — v22.22.2

[4] OmniRush 安装目录
  ✅ app-dist 目录存在  — C:\Users\<你>\AppData\Local\Programs\@omnirushdesktop\resources\app-dist
  ✅ 已定位入口 bundle  — app-DohXHoBv.js

[5] 应用运行状态
  ✅ OmniRush 未运行

[6] bundle 状态
  ✅ bundle 可写
  ⚠️  尚无备份  — 首次运行 apply_all2.py 时会自动建立
  ⚠️  当前状态：官方原版  — 12,324 汉字（汉化后约 38,900）

前置条件满足，有 2 条提醒（不影响使用）。

下一步：python apply_all2.py
```

有 `❌` 就按它给的「→」建议处理，解决后重跑 `doctor.py`。
这个脚本**只读**，不会改动任何文件。

### 关于 `python` 命令

如果提示 `python` 不是内部或外部命令，试这几个：

| 试这个 | 适用情况 |
|---|---|
| `py` | Windows 官方安装包（推荐） |
| `py -3` | 装了多个 Python 版本时 |
| `python3` | 从 Microsoft Store 或某些发行版装的 |

下文一律写 `python`，你按实际情况替换。

---

## 二、三步汉化

### 第 1 步：完全退出 OmniRush

**必须做。** 包括右下角托盘的图标（右键 → 退出）。
应用运行时 bundle 文件可能被占用，覆盖会失败或导致界面异常。

### 第 2 步：运行一键汉化

```bash
cd omnirush-install
python apply_all2.py
```

也可以从任意目录调用：

```bash
python "D:\路径\到\omnirush-zh\omnirush-install\apply_all2.py"
```

**这个脚本是幂等的**——每次运行都先还原官方原版再打补丁，可以反复执行，不会叠加出错。

### 第 3 步：重启 OmniRush

打开后界面就是中文了。

---

## 三、看懂运行输出

正常输出长这样：

```
已从备份还原 -> ...\app-dist\assets\app-DohXHoBv.js
======================================================================
### patch_zh.py
======================================================================
建立原始备份 -> ...\app-DohXHoBv.js.orig-backup     ← 首次运行才有这行
原始 bundle: 5271388 字符
补全版译文: 2078 键
当前 bundle: en 2101 键 | 补全版 zh.ts 2078 键
  ✓ 覆盖率 100%（2078 个普通键 + 23 组复数变体折叠为基键）
[1/2] zh 语言包已替换  (+45773 字符)
[2/2] ENGINE_DETAIL_KEYS 白名单已清空
[3/3] initLocale 回退分支: en -> zh
node --check ✓
写入完成: 5316499 字符
======================================================================
### apply_dict.py
======================================================================
[锚点] 命中 101/106 条，替换 110 处
[模板兜底] 命中 6 条，仍未命中 2 条
[字典] 命中 1175/1182 条，替换 1355 处（字面量合并为 1348 处编辑一次写回）
总长度 5316499 -> 5273739 (-42760)
node --check ✓（本脚本耗时 12.13s）
======================================================================
### 校验
======================================================================
--- verify_syntax.py         ES Module 语法校验通过
--- verify_final.py          键集合一致: True | 值不一致: 0
--- verify_hardcoded.py      残留英文串: 0 | 缺失中文串: 0
--- verify_settings.py       残留英文: 0 | 缺失中文: 0

全部完成 ✅
```

**只要最后一行是「全部完成 ✅」就算成功。** 中途任何脚本失败都会打印 `!!` 并中止，不会写入半成品。

### 想确认汉化效果

```bash
python doctor.py            # 看 [6] bundle 状态 —— 应显示「已汉化 — 38,9xx 汉字」
python list_targets.py      # 列出还没译的英文（正常会剩 20 条左右，都是有意保留的）
```

---

## 四、日常维护

### 应用更新后汉化消失

**这是正常现象，不是出错了。** OmniRush 自动更新会重写整个 `app-dist/`，
把补丁连同备份一起清掉，界面回到官方 55.6% 中文。

**方案 A：装个监视器，让它自己修（推荐）**

```bash
cd omnirush-install
python autorepatch_setup.py --install     # 装开机启动项并立即启动
```

装完之后你**什么都不用管**：它会每 20 秒瞄一眼 bundle，
发现被更新覆盖了（且没汉化）就自动重打。装在
`HKCU\...\Run`，用 `pythonw.exe` 跑，**没有控制台窗口**。

```bash
python autorepatch_setup.py --status      # 看是否在跑 + 最近日志
python autorepatch_setup.py --uninstall   # 不想要了就卸掉
```

> 内存占用约 55 MB。如果你更愿意手动控制，可以不装，
> 每次更新后跑一次 `python apply_all2.py` 就行。

**方案 B：手动重打**

```bash
cd omnirush-install
python doctor.py            # 确认安装路径正常
python apply_all2.py        # 重打一遍
```

两种方案都不需要改任何代码。整套工具不依赖文件名和字节偏移：

- bundle 名字带内容 hash（`app-DohXHoBv.js` → `app-B-rOJfFZ.js`），
  脚本从 `index.html` 的 `<script src>` 自动反查；
- 译文是「内容级」的（英文原文 → 中文），跟偏移无关。

**更新后如果重打失败，多半是官方加了新的 i18n 键**，输出会列出缺哪些键：

```
  en 有但补全版缺译的键: ['session.run_status_working', ...]
!! 补全版覆盖率不足 -> 中止
```

这是**故意拦下来的**，避免静默漏译。按[自定义译文](#六自定义译文进阶)
把缺的键补进 `omnirush-i18n/zh.ts`，再重打即可。

### 换回官方原版 / 卸载

补丁只替换 `resources/app-dist/` 下的一个 js 文件，原版一直保留在备份里。

**还原（在 `omnirush-install` 目录下执行）**：

```bash
python -c "import sys,shutil;sys.path.insert(0,'.');from _bundle import detect_bundle;b=detect_bundle();shutil.copy2(b+'.orig-backup',b);print('已还原:',b)"
```

重启应用即为官方原版。`.orig-backup` 就是官方原版文件，一字未改，
所以还原是 100% 干净的。

> 想彻底卸载？还原后删掉整个 `omnirush-zh` 文件夹即可。
> 本项目没有安装任何常驻程序、没有注册表项、没有开机启动项。

---

## 五、常见问题

### Q1：打开后白屏 / 界面空白

**原因**：bundle 在运行期解析失败，React 没挂载。常见于两种情况：

1. 覆盖 bundle 时应用还在运行 —— 旧进程持有旧代码，或文件写了一半。
2. 补丁本身有语法错误（历史事故，现已由 `verify_syntax.py` 拦住）。

**处理**（命令都在 `omnirush-install` 目录下执行）：

```bash
# 1. 彻底退出 OmniRush（任务管理器里确认没有 OmniRush 进程）
# 2. 还原官方原版
python -c "import sys,shutil;sys.path.insert(0,'.');from _bundle import detect_bundle;b=detect_bundle();shutil.copy2(b+'.orig-backup',b);print('已还原:',b)"
# 3. 重开应用，确认恢复正常
# 4. 重新打补丁
python apply_all2.py
```

如果还原后仍白屏，说明和补丁无关，用官方安装包修复安装。

### Q2：跑完了，界面还是英文

按顺序排查：

| 检查 | 方法 |
|---|---|
| 重启过应用吗？ | 覆盖 bundle 后**必须重启**，热更新不会重载 |
| 补丁真的写入了吗？ | `python doctor.py` 看 [6] 是否显示「已汉化」 |
| 语言设置是中文吗？ | 应用内 设置 → 语言，选「简体中文」 |
| 是不是更新后又覆盖了？ | 看 `app-dist/assets/` 里 bundle 的修改时间 |

### Q3：`!! 找不到 ...index.html`

应用没装在默认位置。编辑 `omnirush-install/_bundle.py`，把 `APP_DIST` 改成你的实际路径：

```python
APP_DIST = r"C:\你的\实际\路径\@omnirushdesktop\resources\app-dist"
```

### Q4：`!! ... 中找不到 app-*.js 入口引用`

应用版本结构变了（官方把入口文件改名了）。
打开 `app-dist/index.html`，找到 `<script type="module" src="./assets/xxx.js">`，
把 `_bundle.py` 里的正则改成匹配这个文件名：

```python
m = re.search(r'src="\./assets/(app-[A-Za-z0-9_-]+\.js)"', html)
#                              ^^^ 改成实际的前缀
```

### Q5：`!! node --check 失败`

补丁生成了语法错误的 bundle，脚本已自动中止、**没有写入**，应用仍是好的。
请提 Issue 并附上完整输出。

### Q6：提示 `'node' 不是内部或外部命令` / `FileNotFoundError: node`

没装 Node.js，或没加进 PATH。到 <https://nodejs.org> 装 LTS 版，
**装完重开终端**（PATH 需要新会话才生效）。装好后 `doctor.py` 的 [3] 会变绿。

### Q7：`PermissionError` / 写入被拒绝

1. 确认 OmniRush 已完全退出（任务管理器里搜 `OmniRush`）；
2. 确认不是把项目放在需要管理员权限的目录；
3. 仍不行就以管理员身份运行终端。

### Q8：杀毒软件报警

补丁会**覆盖应用目录下的 js 文件**，这类行为容易被启发式规则盯上。
如果被拦截，把 `omnirush-install/` 目录和应用目录加入白名单。
本项目不联网、不上传、不写注册表，源码全部公开可查。

### Q9：`!! 补全版覆盖率不足 -> 中止`

应用升级后英文语言包新增了键，而 `omnirush-i18n/zh.ts` 还没补。
输出里会列出缺哪些键。补译后重跑即可，方法见[自定义译文](#六自定义译文进阶)。

### Q10：界面有部分还是英文

分两类：

- **正常情况**：第三方库内部报错（React Router / Zod / KaTeX / Mermaid / shiki 等，
  只在开发者控制台可见）、面向大模型的提示词、产品名（`Google Workspace`、
  `ChatGPT、Claude、Gemini`）——这些**有意保留**。
- **真漏译**：先找出来：

  ```bash
  python list_targets.py          # 排除库区域后的剩余英文清单
  python scan_ui.py               # 按 UI 属性筛选
  python scan_sentences.py        # 按句子特征筛选
  ```

  找到后按[自定义译文](#六自定义译文进阶)补上。

### Q11：老是弹出「重启以更新」，重启后汉化就没了

这是**正常行为**，不用去关自动更新。OmniRush 每天会检查一次更新，
下载完成后提示「重启以更新」；重启安装时会重写 `app-dist/`，汉化随之消失。

两个办法：

1. **装自动重打监视器**（推荐，见[日常维护](#四日常维护)）——
   装一次，以后更新后自动恢复，你什么都不用做。
2. **不装监视器**，每次更新后手动跑一次 `python apply_all2.py`。

> 不建议关自动更新：OmniRush 是活跃开发的工具，新版本常带重要修复。
> 关掉更新反而会积累风险。让它更新、让工具自动补汉化，是更省心的组合。

### Q12：自动重打监视器占多少资源？不想要了怎么卸？

- 每 20 秒做一次文件 `stat`（几乎不耗 CPU），内存约 55 MB
- 卸载：`python autorepatch_setup.py --uninstall`
- 临时停一下：在 `omnirush-install/` 下建一个空文件
  `autorepatch_watch.stop`，它会在下一轮自行退出

---

## 六、自定义译文（进阶）

想改某句译文，或补一条漏译的文案。改完都要重跑 `apply_all2.py` 才生效。

### 情况 A：文案走 i18n（界面上有对应语言键）

改 `omnirush-i18n/zh.ts`：

```ts
"settings.privacy_title": "隐私",
```

改完重跑：

```bash
python apply_all2.py
```

`patch_zh.py` 会把整个语言包重新注入，并校验覆盖率 100%，缺键会直接中止。

### 情况 B：文案硬编码在源码里（不接 i18n）

这类文案在 `zh.ts` 里找不到。加到 `omnirush-install/zh_extra.json`：

```json
{
  "Some hardcoded English sentence.": "对应的中文。"
}
```

- 键 = **bundle 里的英文原文**（逐字符一致，含标点）
- 值 = 中文

重跑 `apply_all2.py`。应用器会按「英文长度降序」套用，不用担心长句被短句打碎。

### 怎么确认原文写对了

在 bundle 里搜：

```bash
python -c "import sys;sys.path.insert(0,'.');from _bundle import detect_bundle;s=open(detect_bundle(),encoding='utf-8').read();kw='你要找的英文';print('出现次数:',s.count(kw));i=s.find(kw);print(repr(s[max(0,i-150):i+150]))"
```

### 情况 C：含 `${}` 插值的文案

压缩产物里的 `${...}` 是变量名/表达式，**换版本就会变**（`${Dt}` → `${xJe}`），
所以不能靠字面量匹配。工具的处理顺序是：

1. 先按字面量整串匹配（同版本内通常直接命中）；
2. 没命中就**模板兜底**：用「文案文本段」在新 bundle 里定位同名模板
   （`${...}` 部分当通配符），再把译文里的旧占位符按顺序换成新的。

你要做的是：把含 `${}` 的英文按**原样**写进 `zh_extra.json`，
译文里保留**同样数量**的 `${...}`（按出现顺序一一对应）。例如：

```json
{
  "Showing ${a} of ${b} results": "显示 ${a} / ${b} 条结果",
  "Connected to ${name}.": "已连接到 ${name}。"
}
```

占位符数量对不上就会跳过（工具不会瞎猜）。

> 兜底要求模板里至少有一段 ≥ 6 字符的纯文本，纯占位符拼接的文案无法定位。

### 改完的验证

```bash
python apply_all2.py        # 看是否「全部完成 ✅」
python list_targets.py      # 看目标文案是否已从剩余清单消失
```

---

## 七、工具速查表

### 日常只用这三个

| 命令 | 作用 |
|---|---|
| `python doctor.py` | **环境自检**（只读）。汉化前先跑 |
| `python apply_all2.py` | **一键汉化**（幂等）。升级后重跑 |
| `python autorepatch_setup.py --install` | **装自动重打**：更新后自动恢复汉化 |
| `python preflight.py` | 项目自检 21 项（本机全量，会实际重打一遍） |

### 排查用

| 命令 | 作用 |
|---|---|
| `python list_targets.py` | 列出还没汉化的英文（整句口径） |
| `python scan_labels.py` | 列出还没汉化的**短标签**（单词标题，≤12 字符那批） |
| `python scan_ui.py` | 按 UI 属性（`placeholder` / `title` 等）扫描 |
| `python scan_sentences.py` | 按句子特征扫描 |
| `python scan_sweep.py` | 宽口径扫描（候选最多） |
| `python check_comparisons.py` | 找出「被 `===` 比较的英文」，防止误译破坏逻辑 |
| `python verify_final.py` | 逐键比对运行时字符串 |
| `python auto_repatch.py --check` | 只检查汉化是否还在（退出码 0=在 1=没了） |

### 校验用（一般不用手动跑，`apply_all2.py` 会自动调）

| 脚本 | 作用 |
|---|---|
| `verify_syntax.py` | ES Module 语法校验（`.mjs` 强制 ESM 解析） |
| `verify_hardcoded.py` | 首页 / 侧栏残留英文检查 |
| `verify_settings.py` | 设置总览页残留英文检查 |
| `modprobe.mjs` | 在 Node 里 import bundle，验证模块求值不抛异常 |

---

## 八、其他平台

目前**只支持 Windows**。补丁脚本里的路径写死了 `%LOCALAPPDATA%`。
macOS / Linux 想用需要自己改两处：

1. `omnirush-install/_bundle.py` 里的 `APP_DIST`：

   | 平台 | 路径 |
   |---|---|
   | macOS | `~/Library/Application Support/@omnirushdesktop/resources/app-dist` |
   | Linux | `~/.config/@omnirushdesktop/resources/app-dist`（视安装方式而定） |

2. `doctor.py` 里用 `tasklist` 查进程的部分（改成 `pgrep` 之类）。

其余逻辑（译文、字典、模板兜底、语法校验）与平台无关，可直接复用。
欢迎提 PR。

---

## 九、安全与可恢复性

- **只动一个文件**：`resources/app-dist/assets/app-<hash>.js`。
  不碰 `app.asar`、不碰安装器、不碰用户数据。
- **官方原版完整保留**：首次运行会建立 `.orig-backup`（与官方文件逐字节一致），
  随时可一键还原。
- **幂等**：每次运行都从原版重来，反复执行结果一致。
- **写入前校验**：语法不过关就中止，绝不写入半成品。
- **不联网**：脚本只读写本地文件。
- **无常驻进程**：没有服务、没有注册表项、没有开机启动项。

---

## 十、还有问题？

- 提 Issue：<https://github.com/liyangru/omnirush-zh/issues>
  请附上 `python doctor.py` 和 `python apply_all2.py` 的完整输出。
- 技术细节与踩坑记录：见 [`omnirush-install/README.md`](omnirush-install/README.md)
