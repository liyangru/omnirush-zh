# -*- coding: utf-8 -*-
"""环境自检：汉化前先跑这个，确认前置条件都满足。

只读操作，不会修改任何文件。逐项给出结论与修复建议。

用法：
    python doctor.py
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

OK, WARN, BAD = "✅", "⚠️ ", "❌"
rows = []


def say(mark, name, detail="", advice=""):
    rows.append((mark, name, detail, advice))
    line = f"  {mark} {name}"
    if detail:
        line += f"  — {detail}"
    print(line)
    if advice and mark != OK:
        print(f"      → {advice}")


print("=" * 72)
print("OmniRush 汉化 —— 环境自检")
print("=" * 72)

# ---------------------------------------------------------------- 1. 平台
print("\n[1] 运行平台")
if os.name == "nt":
    _wv = sys.getwindowsversion()
    say(OK, "Windows", f"{_wv.major}.{_wv.minor} build {_wv.build}")
else:
    say(BAD, f"非 Windows（{os.name}）",
        "补丁脚本按 Windows 路径写死",
        "macOS / Linux 请参考 USAGE.md 的「其他平台」一节自行改路径")

# -------------------------------------------------------------- 2. Python
print("\n[2] Python")
ver = sys.version_info
if ver >= (3, 8):
    say(OK, f"Python {ver.major}.{ver.minor}.{ver.micro}")
else:
    say(BAD, f"Python {ver.major}.{ver.minor}",
        "版本过低",
        "需要 3.8 或更高（脚本用到 f-string、symtable）")

# ---------------------------------------------------------------- 3. Node
print("\n[3] Node.js（语法校验要用）")
node = shutil.which("node")
if node:
    try:
        r = subprocess.run(["node", "--version"], capture_output=True,
                           text=True, timeout=20)
        v = (r.stdout or "").strip()
        say(OK, "node 可用", f"{v}（{node}）")
    except Exception as e:  # noqa: BLE001
        say(WARN, "node 存在但执行失败", str(e)[:80], "检查 Node 安装是否完整")
else:
    say(BAD, "找不到 node",
        "不在 PATH 里",
        "安装 Node.js（https://nodejs.org）后重开终端；"
        "没有它就无法做语法校验，补丁不会写入")

# ------------------------------------------------------- 4. 安装目录 / bundle
print("\n[4] OmniRush 安装目录")
try:
    from _bundle import APP_DIST, detect_bundle
except Exception as e:  # noqa: BLE001
    say(BAD, "无法导入 _bundle.py", str(e)[:80], "确认在 omnirush-install/ 目录下运行")
    detect_bundle = None
    APP_DIST = ""

bundle = None
if detect_bundle:
    if os.path.isdir(APP_DIST):
        say(OK, "app-dist 目录存在", APP_DIST)
    else:
        say(BAD, "找不到 app-dist", APP_DIST,
            "确认已安装 OmniRush 桌面版；若装在别处，改 _bundle.py 里的 APP_DIST")
    try:
        bundle = detect_bundle()
        say(OK, "已定位入口 bundle", os.path.basename(bundle))
    except SystemExit as e:
        say(BAD, "无法定位 bundle", str(e).splitlines()[0][:160],
            "确认安装路径；若装在别处，改 _bundle.py 里的 APP_DIST")
    except Exception as e:  # noqa: BLE001
        say(BAD, "定位 bundle 时出错", f"{type(e).__name__}: {e}"[:160],
            "检查安装目录是否完整")

# -------------------------------------------------------------- 5. 进程状态
print("\n[5] 应用运行状态")
try:
    r = subprocess.run(["tasklist"], capture_output=True, timeout=30)
    # tasklist 在中文 Windows 上是 GBK 输出；用 errors=replace 解码，
    # ASCII 的进程名（OmniRush）不受影响，非 ASCII 部分被替换掉即可。
    out = (r.stdout or b"").decode("utf-8", errors="replace")
    n = len(re.findall(r"OmniRush", out, re.I))
    if n:
        say(WARN, f"OmniRush 正在运行（{n} 个进程）",
            "覆盖 bundle 时文件可能被占用",
            "先完全退出 OmniRush（含托盘图标）再打补丁")
    else:
        say(OK, "OmniRush 未运行")
except Exception as e:  # noqa: BLE001
    say(WARN, "无法查询进程列表", str(e)[:60], "自行确认 OmniRush 已退出")

# -------------------------------------------------------- 6. 可写 / 备份 / 状态
if bundle and os.path.exists(bundle):
    print("\n[6] bundle 状态")
    if os.access(bundle, os.W_OK):
        say(OK, "bundle 可写")
    else:
        say(BAD, "bundle 不可写", "权限不足或文件被占用",
            "关闭应用后重试；必要时以管理员身份运行终端")

    bak = bundle + ".orig-backup"
    if os.path.exists(bak):
        say(OK, "已有官方原版备份", f"{os.path.getsize(bak):,} 字节")
    else:
        say(WARN, "尚无备份", "首次运行 apply_all2.py 时会自动建立")

    src = open(bundle, encoding="utf-8", errors="replace").read()
    han = sum(1 for c in src if "\u4e00" <= c <= "\u9fff")
    marker = "压缩此会话以减少上下文大小" in src
    if marker or han > 25000:
        say(OK, "当前状态：已汉化", f"{han:,} 汉字")
    else:
        say(WARN, "当前状态：官方原版", f"{han:,} 汉字（汉化后约 38,900）",
            "运行 python apply_all2.py 打补丁")

# ------------------------------------------------------------------ 汇总
print()
print("=" * 72)
bad = [r for r in rows if r[0] == BAD]
warn = [r for r in rows if r[0] == WARN]
if bad:
    print(f"发现 {len(bad)} 个阻塞问题，先按上面的建议解决：")
    for _, name, detail, advice in bad:
        print(f"  ❌ {name}" + (f" —— {detail}" if detail else ""))
    print("\n解决后重跑：python doctor.py")
    sys.exit(1)
if warn:
    print(f"前置条件满足，有 {len(warn)} 条提醒（不影响使用）。")
else:
    print("前置条件全部满足 ✅")
print("\n下一步：python apply_all2.py")
