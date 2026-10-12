# -*- coding: utf-8 -*-
"""扫描 bundle 里剩余的「界面短标签」（i18n 数据区之外）。

与 list_targets.py（面向整句）互补：本脚本专门抓 3~160 字符的短标签，
补上旧规则「>=12 字符 + 必须句末标点 + >=3 个单词」漏掉的一大批单词标题。
"""
import re
from _bundle import detect_bundle

B = detect_bundle()
src = open(B, encoding="utf-8").read()
lo = src.find('"account.mcp_connected_one"')
hi = src.find(";function Ws(", lo)

LIB = [
    (0, 274000), (1554000, 1592000), (1785000, 1790000), (2160000, 2240000),
    (2400000, 2480000), (2538000, 2540000), (3580000, 3610000), (3688000, 3692000),
    (3780000, 3783000), (3916000, 3928000), (3993000, 3996000), (4010000, 4014000),
    (4037000, 4040000), (4074000, 4114500), (4215000, 4220000),
]

STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"' r"|'((?:[^'\\\n]|\\.)*)'")
CJK = re.compile(r"[\u4e00-\u9fff]")
SKIP = re.compile(r"(://|^data:|^[a-z]+:|^\.|^/|^@|^--|^var\(|^rgb|^#[0-9a-fA-F]{3,8}$)")
IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")
CODEISH = re.compile(r"(\bfunction\b|\bconst\b|\breturn\b|=>|;\s*$|\(\)|\[|\]|===|!==|\{|\})")
CSSISH = re.compile(
    r"(^|\s)(flex|grid|block|inline|hidden|absolute|relative|sticky|fixed|"
    r"items-|justify-|gap-|px-|py-|pt-|pb-|pl-|pr-|mx-|my-|mt-|mb-|ml-|mr-|"
    r"text-|size-|w-|h-|min-|max-|shrink|grow|truncate|rounded|border|bg-|"
    r"hover:|font-|leading-|tracking-|space-|overflow|z-|opacity-|animate|"
    r"transition|duration|ease-|cursor-|select-|pointer|divide-|ring-|shadow|"
    r"outline|fill-|stroke-|aspect-|object-|order-|col-|row-|basis-|self-|"
    r"place-|content-|inset-|top-|bottom-|left-|right-|whitespace-|break-|"
    r"line-clamp|sr-only|antialiased|uppercase|lowercase|capitalize)(\s|$)")
# 键盘键名 / HTTP 头 / 字体名 / 组件名：不译
KEYS = {
    "Enter", "Escape", "Tab", "Backspace", "Delete", "Insert", "Home", "End",
    "PageUp", "PageDown", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight",
    "CapsLock", "Shift", "Control", "Alt", "Meta", "Space", "NumpadEnter",
    "Content-Type", "Authorization", "Accept", "User-Agent", "Cache-Control",
    "Content-Length", "Cookie", "Set-Cookie", "X-Requested-With", "ETag",
}
FONT = re.compile(r"^[A-Za-z]+\d+-[A-Za-z]+$")
COMPONENT = re.compile(r"^[A-Z][a-z]+(Route|Provider|Context|Store|Manager|Service|"
                       r"Adapter|Handler|Factory|Builder|Client|Server|Registry)$")
PRODUCT = re.compile(
    r"(KaTeX|Mermaid|shiki|React Router|ParseNode|stretchy|loadWasm|"
    r"Google Workspace|ChatGPT|Claude|Gemini|OpenAI|Anthropic|Ollama|"
    r"omnirush|OpenCode|Electron|Sentry|Stripe|Notion|Linear|GitHub|Windows|"
    r"macOS|Linux|JSON|YAML|TOML|HTML|CSS|HTTP|URL|UUID|MCP|API|SDK|CLI|UI|UX)")


def in_lib(o):
    return any(a <= o < b for a, b in LIB)


found = {}
for m in STR.finditer(src):
    o = m.start()
    if lo <= o < hi or in_lib(o):
        continue
    raw = m.group(1) if m.group(1) is not None else m.group(2)
    if raw is None or not (3 <= len(raw) <= 160):
        continue
    if CJK.search(raw) or SKIP.match(raw) or IDENT.match(raw):
        continue
    if not raw[0].isupper():
        continue
    if raw in KEYS or FONT.match(raw) or COMPONENT.match(raw) or PRODUCT.search(raw):
        continue
    if CODEISH.search(raw) or CSSISH.search(raw):
        continue
    found.setdefault(raw, []).append(o)

rows = sorted(found.items(), key=lambda kv: (-len(kv[1]), kv[0]))
print(f"bundle {len(src):,} 字符 | 候选 {len(rows)} 条\n")
for raw, offs in rows:
    print(f"×{len(offs):<3} {raw}")
