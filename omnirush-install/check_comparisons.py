# -*- coding: utf-8 -*-
"""安全检查：在官方原版 bundle 里找出「被 === / !== 比较使用的英文长句」。
这类字符串常被当作状态码/键值，若误译为中文会导致逻辑失效。
"""
import re
from _bundle import detect_bundle

B = detect_bundle() + ".orig-backup"  # noqa
src = open(B, encoding="utf-8").read()

STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'')
CMP = re.compile(r"(===|!==|==|!=)\s*(['\"`])((?:[^'\"`\\\n]|\\.)*)\2")

hits = []
for m in CMP.finditer(src):
    lit = m.group(3)
    if len(lit) < 8 or " " not in lit:
        continue
    if not re.search(r"[A-Za-z]{2}", lit):
        continue
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", lit)
    if len(words) < 3:
        continue
    hits.append((m.start(), m.group(1), lit))

seen = set()
uniq = []
for off, op, lit in hits:
    if lit in seen:
        continue
    seen.add(lit)
    uniq.append((off, op, lit))

print(f"原版中出现在比较运算里的英文长句：{len(uniq)} 条\n")
for off, op, lit in uniq[:80]:
    print(f"  @{off:>9} {op:>3}  {lit[:100]!r}")
