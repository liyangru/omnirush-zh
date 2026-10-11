"""从 minified bundle 中提取「硬编码的英文 UI 文案」候选。

思路：抽取所有字符串字面量，用「前一个属性名」判断它是不是 UI 文案，
再排除掉已经走 i18n 的（出现在 en/zh 语言对象里的值）、CSS 类名、URL、代码等。
"""
import re, json, os, collections, sys
from _bundle import detect_bundle

BUNDLE = detect_bundle()
I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "omnirush-i18n")

UI_PROPS = {
    "children", "title", "subtitle", "label", "description", "placeholder",
    "aria-label", "ariaLabel", "prompt", "tooltip", "heading", "caption",
    "hint", "emptyTitle", "emptyDescription", "confirmLabel", "cancelLabel",
    "alt", "message", "text", "note", "summary", "help", "badge", "name",
    "subtitleText", "body", "cta", "actionLabel", "detail", "sub", "meta",
}

STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"' + r"|'((?:[^'\\]|\\.)*)'" + r"|`((?:[^`\\]|\\.)*)`")
PROP_RE = re.compile(r"([A-Za-z_$][\w$-]*)\s*:\s*$")


def parse_ts(fn):
    t = open(fn, encoding="utf-8").read()
    b = t[t.index("export default {"):]
    return {k: json.loads('"' + v + '"')
            for k, v in re.findall(r'^\s*"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', b, re.M)}


en = parse_ts(os.path.join(I18N, "en.ts"))
zh = parse_ts(os.path.join(I18N, "zh.ts"))
i18n_values = set(en.values()) | set(zh.values())

src = open(BUNDLE, encoding="utf-8").read()

# 语言对象区间：从第一个 en 键到 ru 对象结束（含 zh 对象），这些区域内的字符串都是 i18n 值，跳过
lang_lo = src.find('"account.mcp_connected_one"')
lang_hi = src.find(";function Ws(", lang_lo)
if lang_hi < 0:
    lang_hi = lang_lo
print(f"语言对象区间: [{lang_lo}, {lang_hi}]  ({(lang_hi-lang_lo)//1024} KB)")

SKIP_SUB = ("://", "\\n", "data-", "http", "node_modules", ".js", ".ts", ".json",
            "@", "rgb", "px", "rem", "var(--", "testid")
CSS_HINT = re.compile(r"^[a-z0-9\-\[\]\(\)\.\:\s,/%#!>+~*=&\"']+$")

cands = collections.defaultdict(list)
for m in STR_RE.finditer(src):
    if lang_lo <= m.start() < lang_hi:
        continue
    raw = m.group(1) or m.group(2) or m.group(3)
    if raw is None:
        continue
    if len(raw) < 3 or len(raw) > 160:
        continue
    if raw in i18n_values:
        continue
    if any(s in raw for s in SKIP_SUB):
        continue
    if not re.search(r"[A-Za-z]{2}", raw):
        continue
    # 必须是「像人话」：含空格，或首字母大写且含小写字母，或以 ? ! 结尾
    if not ((" " in raw) or (raw[:1].isupper() and re.search(r"[a-z]", raw)) or raw.rstrip().endswith(("?", "!", "."))):
        continue
    if CSS_HINT.match(raw) and " " not in raw:
        continue
    # 排除全小写多词但明显是 class 的
    if re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)+$", raw):
        continue
    if re.match(r"^[A-Z_]+$", raw):
        continue
    if re.match(r"^[a-z]+\.[a-z_]+$", raw):  # i18n 键名
        continue

    ctx = src[max(0, m.start() - 60):m.start()]
    pm = PROP_RE.search(ctx)
    prop = pm.group(1) if pm else "?"
    cands[prop].append((raw, m.start()))

total = sum(len(v) for v in cands.values())
print(f"\n候选总数: {total}\n")
print("=== 按属性名分布（仅列出 UI 相关属性）===")
for p, items in sorted(cands.items(), key=lambda x: -len(x[1])):
    if p in UI_PROPS:
        print(f"  {p:20s} {len(items)}")

print("\n=== 全部属性名（按数量）===")
for p, items in sorted(cands.items(), key=lambda x: -len(x[1]))[:25]:
    print(f"  {p:24s} {len(items)}")

# 导出 UI 相关候选
ui = []
for p, items in cands.items():
    if p in UI_PROPS:
        for raw, off in items:
            ui.append({"prop": p, "text": raw, "offset": off})
ui.sort(key=lambda x: x["offset"])
json.dump(ui, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "hardcoded_ui.json"),
                   "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nUI 相关候选已导出: {len(ui)} 条 -> hardcoded_ui.json")
uniq = sorted({u["text"] for u in ui})
print(f"去重后: {len(uniq)} 条")
