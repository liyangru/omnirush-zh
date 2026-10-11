# -*- coding: utf-8 -*-
"""可靠地找出 bundle 中「仍然是英文」的 UI 文案（不含 i18n 数据区）。

与旧 scan_hardcoded.py 的区别：
  * 不再用「值是否出现在 en.ts」来过滤（那会把硬编码但同名的文案误杀，
    例如启动卡片的 "Fix a hard bug"）。
  * 改成：扫出所有字符串字面量 -> 排除 i18n 数据区 -> 排除明显非文案的
    （URL / class / 路径 / 标识符 / 纯占位） -> 剩下的按「是否含中文」分类。
"""
import json, os, re, sys, collections
from _bundle import detect_bundle

B = detect_bundle()  # noqa
src = open(B, encoding="utf-8").read()

lang_lo = src.find('"account.mcp_connected_one"')
lang_hi = src.find(";function Ws(", lang_lo)
print(f"i18n 数据区: [{lang_lo}, {lang_hi}]  ({(lang_hi-lang_lo)//1024} KB)\n")

CJK = re.compile(r"[\u4e00-\u9fff]")
# 字符串字面量：双引号 / 单引号 / 反引号
STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
PROP = re.compile(r"([A-Za-z_$][\w$-]*)\s*:\s*$")

# 明显不是 UI 文案的特征（逐条匹配，避免大正则出错）
NOISE_PATTERNS = [
    r"://", r"^data:", r"^https?:", r"\.js$", r"\.ts$", r"\.json$", r"\.css$",
    r"\.svg$", r"\.png$", r"\.md$",
    r"^[a-z0-9._/-]+$",            # 全小写路径 / 标识符
    r"^[A-Za-z0-9+/=]{20,}$",      # base64 / hash
    r"^--", r"^var\(", r"^rgb",
    r"^#[0-9a-fA-F]{3,8}$",
    r"^[a-z-]+(-[a-z0-9]+)+$",     # css class
    r"^[A-Z][A-Za-z0-9]*$",        # 单个驼峰标识符（无空格）
]
NOISE = [re.compile(p) for p in NOISE_PATTERNS]


def is_noise(raw):
    return any(p.match(raw) for p in NOISE)


rows = []
for m in STR.finditer(src):
    if lang_lo <= m.start() < lang_hi:
        continue
    raw = m.group(1) or m.group(2) or m.group(3)
    if raw is None or len(raw) < 4 or len(raw) > 200:
        continue
    if CJK.search(raw):
        continue
    if not re.search(r"[A-Za-z]{2}", raw):
        continue
    if is_noise(raw):
        continue
    if not ((" " in raw.strip()) or raw.rstrip().endswith(("?", "!", "…", ":"))):
        continue
    # 至少 2 个英文单词
    if len(re.findall(r"[A-Za-z]{2,}", raw)) < 2:
        continue
    ctx = src[max(0, m.start() - 80): m.start()]
    pm = PROP.search(ctx)
    prop = pm.group(1) if pm else "?"
    rows.append({"prop": prop, "text": raw, "offset": m.start()})

print(f"疑似仍为英文的文案: {len(rows)} 条")
print(f"去重后: {len({r['text'] for r in rows})} 条\n")

print("=== 按属性名分布 ===")
for p, n in collections.Counter(r["prop"] for r in rows).most_common(20):
    print(f"  {p:24s} {n}")

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remaining_en.json")
json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n已导出 -> {out}")

print("\n=== 前 120 条（按偏移）===")
seen = set()
n = 0
for r in rows:
    if r["text"] in seen:
        continue
    seen.add(r["text"])
    n += 1
    if n > 120:
        break
    print(f"  [{r['prop']:>12}] {r['text'][:95]}")
