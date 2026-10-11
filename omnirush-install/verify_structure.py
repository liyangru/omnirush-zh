# -*- coding: utf-8 -*-
"""结构校验：确认 L2/L3/L4 只改了 i18n 数据区之外的字符串，语言数据区逐字节未变。

做法：
  1. 备份当前（四层全打完）的 bundle
  2. 单独跑 patch_zh.py，得到「只有第 1 层」的 bundle
  3. 分别取出两者的 i18n 数据区，逐字节比对
  4. 还原四层状态
"""
import hashlib, os, shutil, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()
TMP = os.path.join(HERE, "_final_state.js")
PY = sys.executable


def lang_region(path):
    s = open(path, encoding="utf-8").read()
    lo = s.find('"account.mcp_connected_one"')
    hi = s.find(";function Ws(", lo)
    return s[lo:hi], lo, hi


# 1. 备份四层成品
shutil.copy2(BUNDLE, TMP)
print(f"已备份四层成品 -> {TMP}")

# 2. 生成「仅第 1 层」的 bundle
r = subprocess.run([PY, os.path.join(HERE, "patch_zh.py")], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr
print("已生成仅第 1 层的 bundle")

# 3. 比对 i18n 数据区
a, alo, ahi = lang_region(BUNDLE)          # L1 only
b, blo, bhi = lang_region(TMP)             # L1+L2+L3+L4
ha = hashlib.sha256(a.encode("utf-8")).hexdigest()
hb = hashlib.sha256(b.encode("utf-8")).hexdigest()
print(f"\nL1  数据区: [{alo}, {ahi}]  长度 {len(a):,}  sha256 {ha[:16]}")
print(f"成品数据区: [{blo}, {bhi}]  长度 {len(b):,}  sha256 {hb[:16]}")
print(f"\n逐字节一致: {'✅ 是' if a == b else '❌ 否'}")

# 4. 还原四层状态
r = subprocess.run([PY, os.path.join(HERE, "apply_all.py")], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr
print("\n已还原四层成品")
os.remove(TMP)

# 复核
c, _, _ = lang_region(BUNDLE)
print(f"复核成品数据区 sha256: {hashlib.sha256(c.encode('utf-8')).hexdigest()[:16]}  "
      f"{'✅ 与校验前一致' if c == b else '❌ 不一致'}")
