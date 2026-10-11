# -*- coding: utf-8 -*-
"""宽口径终检：找出「首字母大写 + 以句末标点结尾 + 3 个以上英文单词」的句子，
这类几乎必然是给人看的文案。输出后与已知非 UI 清单比对。"""
import re
from _bundle import detect_bundle

B = detect_bundle()  # noqa
src = open(B, encoding="utf-8").read()
lo = src.find('"account.mcp_connected_one"')
hi = src.find(";function Ws(", lo)

STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
CJK = re.compile(r"[\u4e00-\u9fff]")
SKIP = re.compile(r"(://|^data:|^[a-z]+:|^\.|^/|^@|^--|^var\(|^rgb|^#[0-9a-fA-F]{3,8}$)")
IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")

out = []
for m in STR.finditer(src, 0, len(src)):
    if lo <= m.start() < hi:
        continue
    raw = m.group(1) if m.group(1) is not None else (
        m.group(2) if m.group(2) is not None else m.group(3))
    if raw is None or len(raw) < 12 or len(raw) > 500:
        continue
    if CJK.search(raw) or SKIP.match(raw) or IDENT.match(raw):
        continue
    if not raw[0].isupper():
        continue
    if not raw.rstrip().endswith((".", "?", "!", "\u2026")):
        continue
    words = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw)
    if len(words) < 3:
        continue
    # 排除明显代码：含 JS 语法特征
    if re.search(r"(\bfunction\b|\bconst\b|\breturn\b|=>|;\s*$|\{\s*$|\(\)|\[\]|===)", raw):
        continue
    out.append((m.start(), raw))

seen = set()
print(f"高分句子候选 {len(out)} 处")
for off, t in out:
    if t in seen:
        continue
    seen.add(t)
    print(f"@{off:>9}  {t[:150]}")
