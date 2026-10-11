# -*- coding: utf-8 -*-
"""可靠的 bundle 语法校验。

为什么需要这个脚本
------------------
`node --check <file>.js` 在这份 bundle 上会**静默返回 0**（假阳性）：
它是 ESM 产物（`<script type="module">`），但 `export`/`import` 只在文件末尾出现，
Node 的自动模块检测只看文件开头，于是按 CJS 解析并放行。
曾因此让十层补丁全部显示 "node --check ✓"，却带着真实语法错误上线，导致白屏。

本脚本改用 **.mjs 临时文件**强制按 ES Module 解析，能抓出真实错误。
"""
import os, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = detect_bundle()

if not os.path.exists(BUNDLE):
    sys.exit(f"!! 找不到 bundle: {BUNDLE}")

src = open(BUNDLE, encoding="utf-8").read()

# 用 .mjs 后缀强制 ESM 解析
tmp = os.path.join(HERE, "_verify_syntax.mjs")
open(tmp, "w", encoding="utf-8", newline="").write(src)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
os.remove(tmp)

sz = len(src)
han = sum(1 for c in src if "\u4e00" <= c <= "\u9fff")

if r.returncode == 0:
    print(f"✅ ES Module 语法校验通过")
    print(f"   bundle: {sz} 字符 / {han} 个汉字")
    sys.exit(0)

print("❌ 语法校验失败（白屏的直接原因就是这类错误）")
err = (r.stdout or "") + (r.stderr or "")
lines = err.splitlines()
# Node 会把出错的整行巨长代码打出来，只保留头部几行 + 定位行
keep = [l for l in lines if not l.startswith("[Error text truncated")][:12]
for l in keep:
    print(l)
sys.exit(1)
