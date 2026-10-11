# -*- coding: utf-8 -*-
"""精准扫描「可见 UI 文案」：扩大属性白名单 + 识别 JSX 子节点位置。

判定规则（满足其一即视为候选）：
  A. 字符串紧跟在 `propName:` 之后，且 propName 属于 UI_PROPS
  B. 字符串处于 JSX 子节点位置（前面是 `>` 或 `,children:[` 或 `{` + 换行）
排除：CSS 类名、URL、代码标识符、已有中文、纯占位符。

用法: python scan_ui.py [lo hi ...]
"""
import os, re, sys, json, collections
from _bundle import detect_bundle

B = detect_bundle()  # noqa
src = open(B, encoding="utf-8").read()
lang_lo = src.find('"account.mcp_connected_one"')
lang_hi = src.find(";function Ws(", lang_lo)

args = sys.argv[1:]
ranges = [(int(args[i]), int(args[i + 1])) for i in range(0, len(args) - 1, 2)] or [(0, len(src))]

UI_PROPS = {
    # 原有
    "children", "title", "subtitle", "label", "description", "placeholder",
    "aria-label", "ariaLabel", "prompt", "tooltip", "heading", "caption",
    "hint", "emptyTitle", "emptyDescription", "confirmLabel", "cancelLabel",
    "alt", "message", "text", "note", "summary", "help", "badge", "cta",
    "subtitleText", "body", "actionLabel", "detail", "sub", "meta",
    # 扩充：命名 / 说明 / 行动按钮 / 状态 / 错误 / 空态
    "name", "desc", "descriptionText", "summaryText", "detailText",
    "instructions", "setupInstructions", "setupTitle", "setupDetail",
    "primaryCta", "secondaryCta", "tertiaryCta", "ctaLabel", "ctaText",
    "actionText", "actionName", "buttonLabel", "buttonText", "okText",
    "cancelText", "submitLabel", "confirmText", "dismissLabel", "closeLabel",
    "error", "errorMessage", "errorText", "warning", "warningText",
    "toast", "toastMessage", "toastText", "statusText", "statusLabel",
    "successMessage", "infoText", "loadingText", "loadingLabel", "emptyText",
    "emptyLabel", "emptyMessage", "reason", "reasonText", "footerText",
    "headerText", "headerTitle", "sectionTitle", "groupTitle", "tabTitle",
    "pageTitle", "modalTitle", "dialogTitle", "panelTitle", "cardTitle",
    "cardDescription", "itemTitle", "itemDescription", "optionLabel",
    "optionDescription", "valueLabel", "unitLabel", "helperText", "footnote",
    "disclaimer", "legalText", "notice", "alert", "alertText", "bannerText",
    "stepTitle", "stepDescription", "taskLabel", "activityLabel", "phaseLabel",
    "verb", "verbLabel", "pastTense", "presentTense", "gerund", "statusPhrase",
}

STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"|\'((?:[^\'\\\n]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')
PROP = re.compile(r"([A-Za-z_$][\w$-]*)\s*:\s*$")
JSX = re.compile(r"(?:>\s*|children:\s*\[\s*|\{\s*)$")
CJK = re.compile(r"[\u4e00-\u9fff]")
CSS_TOKEN = re.compile(r"^-?[a-z0-9]+(-[a-z0-9./[\]%()#:,]+)*$")
SKIP = re.compile(r"(://|^data:|^[a-z]+:|^\.|^/|^@|^--|^var\(|^rgb|^#[0-9a-fA-F]{3,8}$)")
IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")
# SVG path 数据
SVGPATH = re.compile(r"^[Mm]?\s*-?\d+(\.\d+)?[\s,]")


def is_style(s):
    parts = s.split()
    if not parts or len(parts) > 14:
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
        if raw is None or len(raw) < 3 or len(raw) > 400:
            continue
        if CJK.search(raw) or SKIP.match(raw) or IDENT.match(raw):
            continue
        if is_style(raw) or SVGPATH.match(raw):
            continue
        words = re.findall(r"[A-Za-z][A-Za-z'\-]*", raw)
        if not words:
            continue
        ctx = src[max(0, m.start() - 90): m.start()]
        pm = PROP.search(ctx)
        prop = pm.group(1) if pm else None
        is_jsx = bool(JSX.search(ctx))
        if prop not in UI_PROPS and not is_jsx:
            continue
        # 至少 2 个英文单词，或单个词但首字母大写（短标签）
        if len(words) < 2 and not raw[:1].isupper():
            continue
        rows.append((prop or "<jsx>", m.start(), raw))

print(f"区间 {ranges}  命中 {len(rows)} 处")
print("\n=== 属性分布 ===")
for p, n in collections.Counter(r[0] for r in rows).most_common(25):
    print(f"  {p:22s} {n}")

seen = set()
uniq = []
for prop, off, t in rows:
    if t in seen:
        continue
    seen.add(t)
    uniq.append({"prop": prop, "text": t, "offset": off})

print("\n=== 明细 ===")
for it in uniq:
    print(f"[{it['prop']:>16}] @{it['offset']:>9}  {it['text'][:120]}")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_sweep.json")
json.dump(uniq, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n去重 {len(uniq)} 条 -> {out}")
