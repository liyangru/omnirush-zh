# -*- coding: utf-8 -*-
"""终检扫描：不做属性白名单限制，只排除明显的代码/样式/URL，
输出所有「看起来像给人看的英文句子」的字符串，供人工复核。

用法: python scan_sweep.py [lo hi ...]
"""
import os, re, sys, json
from _bundle import detect_bundle

B = detect_bundle()  # noqa
src = open(B, encoding="utf-8").read()
lang_lo = src.find('"account.mcp_connected_one"')
lang_hi = src.find(";function Ws(", lang_lo)

args = sys.argv[1:]
ranges = [(int(args[i]), int(args[i + 1])) for i in range(0, len(args) - 1, 2)] or [(0, len(src))]

STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
CJK = re.compile(r"[\u4e00-\u9fff]")

# 明显是代码 / 样式 / 数据，不是文案
CSS_TOKEN = re.compile(r"^-?[a-z0-9]+(-[a-z0-9./[\]%()#:,]+)*$")
SKIP = re.compile(
    r"(://|^data:|^[a-z]+:|^\.|^/|^@|^--|^var\(|^rgb|^#[0-9a-fA-F]{3,8}$|"
    r"^[A-Za-z0-9+/=_-]{16,}$|"
    r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$)")
IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")


def is_style(s):
    """整串由 CSS class 组成（含空格分隔的多个 class）"""
    parts = s.split()
    if not parts or len(parts) > 12:
        return False
    return all(CSS_TOKEN.match(p) or p.startswith("!") or "[" in p or ":" in p
               or p.startswith("data-") for p in parts)


rows = []
for lo, hi in ranges:
    for m in STR.finditer(src, lo, hi):
        if lang_lo <= m.start() < lang_hi:
            continue
        raw = m.group(1) if m.group(1) is not None else (
            m.group(2) if m.group(2) is not None else m.group(3))
        if raw is None or len(raw) < 6 or len(raw) > 400:
            continue
        if CJK.search(raw):
            continue
        if SKIP.match(raw) or IDENT.match(raw) or is_style(raw):
            continue
        # 必须像句子：至少 2 个英文单词，且含空格
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw)
        if len(words) < 2 or " " not in raw:
            continue
        if not re.search(r"[A-Za-z]{2}", raw):
            continue
        rows.append((m.start(), raw))

seen = set()
uniq = []
for off, t in rows:
    if t in seen:
        continue
    seen.add(t)
    uniq.append({"offset": off, "text": t})

print(f"区间 {ranges}  候选 {len(rows)} 处 / 去重 {len(uniq)} 条\n")
for it in uniq:
    print(f"@{it['offset']:>9}  {it['text'][:130]}")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep.json")
json.dump(uniq, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n-> {out}")
