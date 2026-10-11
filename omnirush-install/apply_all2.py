# -*- coding: utf-8 -*-
"""一键重打汉化（与 bundle 文件名/偏移无关，应用升级后照样可用）。

流程：
  1. 从 .orig-backup 还原官方原版（没有备份就以当前 bundle 建立）
  2. patch_zh.py    —— 注入补全版 zh 语言包（2078 键）+ 清空白名单 + 默认中文
  3. apply_dict.py  —— 套用 zh_dict.json / zh_anchors.json / zh_extra.json 的内容级译文
  4. verify_syntax.py —— ES Module 语法校验（.mjs，杜绝 .js 假阳性）

幂等：每次都从原版重来，可反复执行。
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
from _bundle import detect_bundle, backup_path

BUNDLE = detect_bundle()
BAK = backup_path()
CHECKS = ["patch_zh.py", "apply_dict.py"]
VERIFY = ["verify_syntax.py", "verify_final.py",
          "verify_hardcoded.py", "verify_settings.py"]

# 1. 还原
if os.path.exists(BAK):
    shutil.copy2(BAK, BUNDLE)
    print(f"已从备份还原 -> {BUNDLE}")
else:
    shutil.copy2(BUNDLE, BAK)
    print(f"建立原始备份 -> {BAK}")

ok = True
for script in CHECKS:
    print("\n" + "=" * 72)
    print(f"### {script}")
    print("=" * 72)
    r = subprocess.run([PY, os.path.join(HERE, script)], cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8")
    print((r.stdout or "").rstrip())
    if r.returncode != 0:
        print((r.stderr or "").rstrip())
        ok = False
        break

if ok:
    print("\n" + "=" * 72)
    print("### 校验")
    print("=" * 72)
    for script in VERIFY:
        r = subprocess.run([PY, os.path.join(HERE, script)], cwd=HERE,
                           capture_output=True, text=True, encoding="utf-8")
        out = "\n".join(l for l in (r.stdout or "").splitlines()
                        if l.strip())
        print(f"--- {script}")
        print(out)
        if r.returncode != 0:
            ok = False

print("\n" + ("全部完成 ✅" if ok else "!! 存在问题，请检查上面的输出"))
sys.exit(0 if ok else 1)
