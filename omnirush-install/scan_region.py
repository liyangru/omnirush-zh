# -*- coding: utf-8 -*-
"""按区域扫描 bundle 中仍为英文的 UI 文案（用于逐屏补漏）。

用法: python scan_region.py <lo> <hi> [lo2 hi2 ...]
"""
import os, re, sys, collections
from _bundle import detect_bundle

B = detect_bundle()  # noqa
src = open(B, encoding="utf-8").read()
lang_lo = src.find('"account.mcp_connected_one"')
lang_hi = src.find(";function Ws(", lang_lo)

ranges = []
args = sys.argv[1:]
for i in range(0, len(args) - 1, 2):
    ranges.append((int(args[i]), int(args[i + 1])))
if not ranges:
    ranges = [(0, len(src))]

UI_PROPS = {
    "children", "title", "subtitle", "label", "description", "placeholder",
    "aria-label", "ariaLabel", "prompt", "tooltip", "heading", "caption",
    "hint", "emptyTitle", "emptyDescription", "confirmLabel", "cancelLabel",
    "alt", "message", "text", "note", "summary", "help", "badge", "cta",
    "subtitleText", "body", "actionLabel", "detail", "sub", "meta",
}
STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
PROP = re.compile(r"([A-Za-z_$][\w$-]*)\s*:\s*$")
CJK = re.compile(r"[\u4e00-\u9fff]")
NOISE = re.compile(
    r"(://|^data:|^https?:|\.js$|\.ts$|\.json$|\.css$|\.svg$|\.png$|\.md$|"
    r"^[a-z0-9._/-]+$|^[A-Za-z0-9+/=]{20,}$|^--|^var\(|^rgb|^#[0-9a-fA-F]{3,8}$|"
    r"^[a-z-]+(-[a-z0-9]+)+$|^[A-Z][A-Za-z0-9]*$)")
DEV = re.compile(r"(profiler|watchdog|Cmd\+Shift|__omnirush|reactRender)")

rows = []
for lo, hi in ranges:
    for m in STR.finditer(src, lo, hi):
        if lang_lo <= m.start() < lang_hi:
            continue
        raw = m.group(1) or m.group(2) or m.group(3)
        if raw is None or len(raw) < 4 or len(raw) > 200:
            continue
        if CJK.search(raw) or not re.search(r"[A-Za-z]{2}", raw):
            continue
        if NOISE.match(raw) or DEV.search(raw):
            continue
        if len(re.findall(r"[A-Za-z]{2,}", raw)) < 2:
            continue
        if not ((" " in raw.strip()) or raw.rstrip().endswith(("?", "!", "…", ":"))):
            continue
        ctx = src[max(0, m.start() - 80): m.start()]
        pm = PROP.search(ctx)
        prop = pm.group(1) if pm else "?"
        if prop not in UI_PROPS:
            continue
        rows.append((prop, m.start(), raw))

print(f"区间 {ranges}  命中 {len(rows)} 条")
print("\n=== 属性分布 ===")
for p, n in collections.Counter(r[0] for r in rows).most_common(15):
    print(f"  {p:22s} {n}")

print("\n=== 明细 ===")
seen = set()
uniq = []
for prop, off, t in rows:
    if t in seen:
        continue
    seen.add(t)
    uniq.append({"prop": prop, "text": t, "offset": off})
    print(f"[{prop:>12}] @{off:>8} {t[:105]}")

import json
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remaining2.json")
json.dump(uniq, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n去重 {len(uniq)} 条 -> {out}")
