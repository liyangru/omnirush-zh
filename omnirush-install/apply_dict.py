# -*- coding: utf-8 -*-
"""与偏移无关的汉化应用器：把 zh_dict.json / zh_anchors.json 套到当前 bundle。

适用于应用自动更新后 bundle 文件名与字节偏移全变的情况。

机制
----
1. 先套「复合锚点」（整段代码片段替换，语境更精确）；
2. 再套「平铺字典」，**英文按长度从长到短**排序，避免短句先替换把长句打碎
   （例如 "Same as main agent" 必须晚于包含它的整句）；
3. 定界符自动识别：依次尝试 "…" / '…' / `…`，取第一个有命中的形式；
4. **全程避开 i18n 数据区**，官方十种语言包的英文原文一字不动；
5. 写入前用 .mjs 临时文件做 ES Module 语法校验（.js 会假阳性）。
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
from _bundle import detect_bundle

BUNDLE = detect_bundle()
BAK = BUNDLE + ".orig-backup"

src = open(BUNDLE, encoding="utf-8").read()
LO = src.find('"account.mcp_connected_one"')
HI = src.find(";function Ws(", LO)
if LO < 0 or HI < 0:
    sys.exit("!! 定位不到 i18n 数据区")

D = json.load(open(os.path.join(HERE, "zh_dict.json"), encoding="utf-8"))
ANCHORS = json.load(open(os.path.join(HERE, "zh_anchors.json"), encoding="utf-8"))
# 补充字典：应用升级后新出现的文案
_extra_path = os.path.join(HERE, "zh_extra.json")
if os.path.exists(_extra_path):
    D.update(json.load(open(_extra_path, encoding="utf-8")))
    print(f"已合并补充字典 zh_extra.json")

orig_len = len(src)


def protected_replace(text, old, new):
    """只在 i18n 数据区之外替换，返回 (新文本, 替换次数)。

    i18n 区内容从头到尾不会被改动，所以每次调用都重新定位边界；
    逐处判断当前偏移是否落在区内，避免边界随替换漂移。
    """
    lo = text.find('"account.mcp_connected_one"')
    hi = text.find(";function Ws(", lo) if lo >= 0 else -1
    out = []
    total = 0
    i = 0
    while True:
        j = text.find(old, i)
        if j < 0:
            out.append(text[i:])
            break
        if lo >= 0 and lo <= j < hi:
            out.append(text[i:j + len(old)])   # 区内原样保留
            i = j + len(old)
            continue
        out.append(text[i:j])
        out.append(new)
        total += 1
        i = j + len(old)
    return "".join(out), total


# ---------- 1. 复合锚点 ----------
a_hit = a_miss = a_cnt = 0
missed_anchors = []
for old, new in ANCHORS:
    src, n = protected_replace(src, old, new)
    if n:
        a_hit += 1
        a_cnt += n
    else:
        a_miss += 1
        missed_anchors.append(old)
print(f"[锚点] 命中 {a_hit}/{len(ANCHORS)} 条，替换 {a_cnt} 处")
if a_miss:
    print(f"       未命中 {a_miss} 条（新版可能已改动）：")
    for m in missed_anchors[:10]:
        print(f"         · {m[:88]}")

# ---------- 2. 平铺字典（长句优先） ----------
items = sorted(D.items(), key=lambda kv: -len(kv[0]))
d_hit = d_miss = d_cnt = 0
missed = []


def in_i18n(text, pos):
    lo = text.find('"account.mcp_connected_one"')
    hi = text.find(";function Ws(", lo) if lo >= 0 else -1
    return lo >= 0 and lo <= pos < hi


def split_tmpl(s):
    """把模板字面量内容拆成 [('text',..)/('ph',..)]，ph 含 ${...}"""
    out, i, n = [], 0, len(s)
    buf = ""
    while i < n:
        if s[i] == "$" and i + 1 < n and s[i + 1] == "{":
            if buf:
                out.append(("text", buf))
                buf = ""
            depth, j = 0, i + 1
            while j < n:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            out.append(("ph", s[i:j + 1]))
            i = j + 1
        else:
            buf += s[i]
            i += 1
    if buf:
        out.append(("text", buf))
    return out


def apply_template(text, en, zh):
    """按文本段对齐，在新 bundle 里定位同名模板字面量并把占位符重映射后替换。

    压缩产物里的 ${...} 是变量名/表达式，换版本就变；但包裹它的文案不变。
    所以用文案文本段定位，再把旧占位符换成新的。
    """
    # 译文可能自带定界符（字典里存的是完整字面量），先剥掉
    for d in ('"', "'", "`"):
        if zh.startswith(d) and zh.endswith(d) and len(zh) >= 2:
            zh = zh[1:-1]
    toks = split_tmpl(en)
    texts = [t for k, t in toks if k == "text"]
    if not any(len(t) >= 6 for t in texts):
        return text, 0
    anchor = max((t for t in texts if t), key=len)
    # 用「长文本段 + 通配 + 其余文本段」拼出正则
    parts = []
    for k, t in toks:
        if k == "text":
            parts.append(re.escape(t))
        else:
            parts.append(r"\$\{(?:[^{}`]|\{[^{}`]*\})*\}")
    pat = re.compile("".join(parts))
    total = 0
    while True:
        m = None
        for cand in pat.finditer(text):
            if not in_i18n(text, cand.start()):
                m = cand
                break
        if not m:
            break
        s, e = m.start(), m.end()
        # 确认被反引号包裹
        if s == 0 or text[s - 1] != "`" or e >= len(text) or text[e] != "`":
            return text, total
        new_lit = text[s:e]
        new_phs = re.findall(r"\$\{(?:[^{}`]|\{[^{}`]*\})*\}", new_lit)
        old_phs = [t for k, t in toks if k == "ph"]
        old_zh_phs = [t for k, t in split_tmpl(zh) if k == "ph"]
        if len(new_phs) != len(old_zh_phs):
            return text, total
        new_zh = zh
        # 从后往前替换译文里的占位符，避免相互干扰
        for a, b in reversed(list(zip(old_zh_phs, new_phs))):
            idx = new_zh.rfind(a)
            if idx < 0:
                return text, total
            new_zh = new_zh[:idx] + b + new_zh[idx + len(a):]
        text = text[:s - 1] + "`" + new_zh + "`" + text[e + 1:]
        total += 1
        if total > 50:
            break
    return text, total


for en, zh in items:
    # 防御：译文不得自带定界符（曾经的 bug）
    for d in ('"', "'", "`"):
        if zh.startswith(d) and zh.endswith(d) and len(zh) >= 2:
            zh = zh[1:-1]
    done = False
    # 依次尝试三种定界符，取第一个真的有命中的。
    # 注意：不能因为内容含反引号就只试反引号——含反引号的文案也可能是
    # 双引号字符串（例如 Entries include `pinned`, ...）。
    for d in ('"', "'", "`"):
        # " 和 ' 不能出现在译文里；反引号只要成对（嵌套模板）就可以
        if d in ('"', "'") and d in zh:
            continue
        if d == "`" and zh.count("`") % 2 != 0:
            continue
        lit = d + en + d
        new_lit = d + zh + d
        src, n = protected_replace(src, lit, new_lit)
        if n:
            d_hit += 1
            d_cnt += n
            done = True
            break
    if not done:
        missed.append(en)

# ---------- 2b. 模板字面量兜底：${...} 里是压缩变量名，换版本即失效 ----------
tmpl_ok = tmpl_bad = 0
still = []
for en in missed:
    if "${" not in en:
        still.append(en)
        continue
    src, n = apply_template(src, en, D[en])
    if n:
        d_hit += 1
        d_cnt += n
        tmpl_ok += 1
    else:
        tmpl_bad += 1
        still.append(en)
if tmpl_ok or tmpl_bad:
    print(f"[模板兜底] 命中 {tmpl_ok} 条，仍未命中 {tmpl_bad} 条")
missed = still

print(f"[字典] 命中 {d_hit}/{len(items)} 条，替换 {d_cnt} 处")
print(f"       未命中 {d_miss} 条")
for m in missed[:40]:
    print(f"         · {m[:96]}")

print(f"\n总长度 {orig_len} -> {len(src)} ({len(src)-orig_len:+d})")

# ---------- 3. 语法校验（.mjs 强制 ESM）----------
tmp = BUNDLE + ".tmpcheck.mjs"
open(tmp, "w", encoding="utf-8", newline="").write(src)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    keep = os.path.join(HERE, "_dbg_failed.mjs")
    open(keep, "w", encoding="utf-8", newline="").write(src)
    os.remove(tmp)
    err = (r.stdout or "") + (r.stderr or "")
    lines = [l for l in err.splitlines() if not l.startswith("[Error text truncated")]
    print("!! node --check 失败：")
    for l in lines[:10]:
        print("   ", l[:200])
    print(f"   现场已保留 -> {keep}")
    sys.exit(1)
os.remove(tmp)
print("node --check ✓")

open(BUNDLE, "w", encoding="utf-8", newline="").write(src)
print(f"已写入 {BUNDLE}")
