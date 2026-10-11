# -*- coding: utf-8 -*-
"""列出应用自身代码区（排除第三方库）里剩余的高分英文句子，输出完整文本。"""
import re
from _bundle import detect_bundle

B = detect_bundle()  # noqa
src = open(B, encoding="utf-8").read()
lo = src.find('"account.mcp_connected_one"')
hi = src.find(";function Ws(", lo)

# 第三方库区域（不含应用 UI）
LIB = [
    (0, 274000),            # React Router / Zod / misc
    (1554000, 1592000),     # AI SDK
    (1785000, 1790000),     # 排版库
    (2160000, 2240000),     # VSCode disposables / terminal
    (2400000, 2480000),     # xterm
    (2538000, 2540000),     # react-resizable-panels
    (3580000, 3610000),     # wasm / shiki
    (3688000, 3692000),     # shiki
    (3780000, 3783000),     # KaTeX
    (3916000, 3928000),     # KaTeX
    (3993000, 3996000),     # KaTeX
    (4010000, 4014000),     # KaTeX
    (4037000, 4040000),     # Mermaid 库
    (4074000, 4114500),     # MCP SDK + MCP Apps SDK 类型文档
    (4215000, 4220000),     # 库
]

STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
CJK = re.compile(r"[\u4e00-\u9fff]")
SKIP = re.compile(r"(://|^data:|^[a-z]+:|^\.|^/|^@|^--|^var\(|^rgb|^#[0-9a-fA-F]{3,8}$)")
IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")


def in_lib(o):
    return any(a <= o < b for a, b in LIB)


rows = []
for m in STR.finditer(src, 0, len(src)):
    o = m.start()
    if lo <= o < hi or in_lib(o):
        continue
    d = src[o]
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
    if len(re.findall(r"[A-Za-z][A-Za-z'\-]*", raw)) < 3:
        continue
    if re.search(r"(\bfunction\b|\bconst\b|\breturn\b|=>|;\s*$|\{\s*$|\(\)|\[\]|===)", raw):
        continue
    rows.append((o, d, raw))

seen = set()
uniq = []
for o, d, t in rows:
    if t in seen:
        continue
    seen.add(t)
    uniq.append((o, d, t))

print(f"候选 {len(uniq)} 条\n")
for o, d, t in uniq:
    print(f"@@{o}|{d}|{t}")
