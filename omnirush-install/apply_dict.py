# -*- coding: utf-8 -*-
"""与偏移无关的汉化应用器：把 zh_dict.json / zh_anchors.json / zh_extra.json 套到当前 bundle。

适用于应用自动更新后 bundle 文件名与字节偏移全变的情况。

机制
----
1. **复合锚点**：整段代码片段替换，语境比单词替换更精确；
2. **含 ${} 的条目走模板兜底**：压缩产物里的 `${...}` 是变量名/表达式，换版本就变
   （`${Dt}` → `${xJe}`），但包裹它的文案不变。用文案文本段定位，再把旧占位符映射成新的。
   这一步必须**早于**字面量批量替换 —— 否则整句模板里的 `"Same as main agent"`
   会先被单独替换掉，模板就再也匹配不上了；
3. **其余条目批量替换**：先把所有命中位置找齐（不重建字符串），去重叠后**一次写回**；
4. 定界符自动识别：依次尝试 "…" / '…' / `…`，取第一个有命中的形式；
5. **全程避开 i18n 数据区**，官方十种语言包的英文原文一字不动；
6. 写入前用 .mjs 临时文件做 ES Module 语法校验（.js 会假阳性）。

性能
----
i18n 区内容全程不变，边界只定位一次、按替换长度差增量平移。
字面量替换改为「找齐 → 去重叠 → 一次写回」：早期版本每命中一条就重建整个
5.3 MB 字符串（约 1175 次、每次搬 10 MB），光这一项就要 12 秒；
现在只重建一次。整体从约 27 秒降到 5 秒以内，且输出逐字节一致。
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
from _bundle import detect_bundle

BUNDLE = detect_bundle()
BAK = BUNDLE + ".orig-backup"

LANG_ANCHOR_LO = '"account.mcp_connected_one"'
LANG_ANCHOR_HI = ";function Ws("


def strip_delims(zh):
    """译文可能自带定界符（字典里存的是完整字面量），剥掉一层。"""
    for d in ('"', "'", "`"):
        if zh.startswith(d) and zh.endswith(d) and len(zh) >= 2:
            zh = zh[1:-1]
    return zh


class Bundle:
    """持有 bundle 文本 + 缓存的 i18n 数据区边界（随替换增量平移）。"""

    def __init__(self, text):
        self.s = text
        self.lo = text.find(LANG_ANCHOR_LO)
        self.hi = text.find(LANG_ANCHOR_HI, self.lo) if self.lo >= 0 else -1
        if self.lo < 0 or self.hi < 0:
            sys.exit("!! 定位不到 i18n 数据区（锚点变了？检查 LANG_ANCHOR_*）")

    def _shift(self, delta, before_lo):
        if before_lo:
            self.lo += delta
            self.hi += delta

    def replace_outside(self, old, new):
        """逐条替换（锚点用：只有 100 多条，重建开销可接受）。"""
        s, lo, hi = self.s, self.lo, self.hi
        out, i, total, n_before = [], 0, 0, 0
        L = len(old)
        while True:
            j = s.find(old, i)
            if j < 0:
                out.append(s[i:])
                break
            if lo <= j < hi:                      # 区内原样保留
                out.append(s[i:j + L])
                i = j + L
                continue
            out.append(s[i:j])
            out.append(new)
            total += 1
            if j < lo:
                n_before += 1
            i = j + L
        if total:
            self.s = "".join(out)
            self._shift((len(new) - L) * n_before, n_before > 0)
        return total

    def find_outside(self, lit):
        """找出 lit 在 i18n 区之外的全部位置（不改字符串）。"""
        s, lo, hi = self.s, self.lo, self.hi
        pos, i = [], -1
        while True:
            i = s.find(lit, i + 1)
            if i < 0:
                break
            if lo <= i < hi:
                continue
            pos.append(i)
        return pos

    def apply_edits(self, edits):
        """批量写回（只重建一次）。edits: [(start, end, new)]，允许重叠，
        同起点优先保留更长的 —— 条目已按英文长度降序处理，等价于「长句优先」。"""
        edits = sorted(edits, key=lambda e: (e[0], -(e[1] - e[0])))
        kept, last_end = [], -1
        for e in edits:
            if e[0] >= last_end:
                kept.append(e)
                last_end = e[1]
        if not kept:
            return 0
        parts, prev = [], 0
        for st, en_, new in kept:
            parts.append(self.s[prev:st])
            parts.append(new)
            prev = en_
        parts.append(self.s[prev:])
        self.s = "".join(parts)
        before = [(st, en_, new) for st, en_, new in kept if st < self.lo]
        if before:
            self._shift(sum(len(n) - (e - st) for st, e, n in before), True)
        return len(kept)

    def replace_span(self, start, end, new):
        delta = len(new) - (end - start)
        self.s = self.s[:start] + new + self.s[end:]
        self._shift(delta, start < self.lo)
        return delta


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


PH_RE = re.compile(r"\$\{(?:[^{}`]|\{[^{}`]*\})*\}")
PH_ANY = r"\$\{(?:[^{}`]|\{[^{}`]*\})*\}"


def apply_template(bundle, en, zh):
    """按文本段对齐定位同名模板字面量，把旧占位符映射成新的后替换。"""
    zh = strip_delims(zh)
    toks = split_tmpl(en)
    texts = [t for k, t in toks if k == "text"]
    if not any(len(t) >= 6 for t in texts):
        return 0
    pat = re.compile("".join(
        re.escape(t) if k == "text" else PH_ANY for k, t in toks))
    old_zh_phs = [t for k, t in split_tmpl(zh) if k == "ph"]
    total = 0
    while total <= 50:
        m = None
        for cand in pat.finditer(bundle.s):
            if not (bundle.lo <= cand.start() < bundle.hi):
                m = cand
                break
        if not m:
            break
        s, e = m.start(), m.end()
        if s == 0 or bundle.s[s - 1] != "`" or e >= len(bundle.s) or bundle.s[e] != "`":
            break
        new_phs = PH_RE.findall(bundle.s[s:e])
        if len(new_phs) != len(old_zh_phs):
            break
        new_zh = zh
        for a, b in reversed(list(zip(old_zh_phs, new_phs))):
            idx = new_zh.rfind(a)
            if idx < 0:
                return total
            new_zh = new_zh[:idx] + b + new_zh[idx + len(a):]
        bundle.replace_span(s - 1, e + 1, "`" + new_zh + "`")
        total += 1
    return total


T0 = time.perf_counter()
bundle = Bundle(open(BUNDLE, encoding="utf-8").read())
orig_len = len(bundle.s)

D = json.load(open(os.path.join(HERE, "zh_dict.json"), encoding="utf-8"))
ANCHORS = json.load(open(os.path.join(HERE, "zh_anchors.json"), encoding="utf-8"))
_extra = os.path.join(HERE, "zh_extra.json")
if os.path.exists(_extra):
    D.update(json.load(open(_extra, encoding="utf-8")))
    print("已合并补充字典 zh_extra.json")

# ---------- 1. 复合锚点（逐条替换：条数少，且后续字典替换依赖它先完成）----------
a_hit = a_cnt = 0
missed_anchors = []
for old, new in ANCHORS:
    n = bundle.replace_outside(old, new)
    if n:
        a_hit += 1
        a_cnt += n
    else:
        missed_anchors.append(old)
print(f"[锚点] 命中 {a_hit}/{len(ANCHORS)} 条，替换 {a_cnt} 处")
if missed_anchors:
    print(f"       未命中 {len(missed_anchors)} 条（新版可能已改动）：")
    for m in missed_anchors[:10]:
        print(f"         · {m[:88]}")

# ---------- 2. 平铺字典（长句优先）----------
items = [(en, strip_delims(zh))
         for en, zh in sorted(D.items(), key=lambda kv: -len(kv[0]))]
d_hit = d_cnt = 0
missed = []

# 2a. 字面量批量替换：找齐所有命中位置，去重叠后一次写回。
#     条目已按英文长度降序排列，去重叠时「同起点保留更长者」正好等价于「长句优先」——
#     例如整句模板 `` `How hard sub-agents think. "Same as main agent" uses …` ``
#     会覆盖它内部那句 "Same as main agent"，与逐条替换的效果一致。
edits = []
for en, zh in items:
    for d in ('"', "'", "`"):
        # " 和 ' 不能出现在译文里；反引号只要成对（嵌套模板）就可以
        if d in ('"', "'") and d in zh:
            continue
        if d == "`" and zh.count("`") % 2 != 0:
            continue
        lit = d + en + d
        pos = bundle.find_outside(lit)
        if pos:
            new_lit = d + zh + d
            edits.extend((p, p + len(lit), new_lit) for p in pos)
            d_hit += 1
            d_cnt += len(pos)
            break
    else:
        missed.append(en)
n_edits = bundle.apply_edits(edits)

# 2b. 模板兜底：字面量没匹配上的、含 ${} 的条目。
#     压缩产物里的 ${...} 是变量名/表达式，换版本就变（${Dt} → ${xJe}），
#     字面量匹配必然失败；改用文案文本段定位，再把旧占位符映射成新的。
tmpl_ok = tmpl_bad = 0
still = []
for en in missed:
    if "${" not in en:
        still.append(en)
        continue
    if apply_template(bundle, en, D[en]):
        d_hit += 1
        d_cnt += 1
        tmpl_ok += 1
    else:
        tmpl_bad += 1
        still.append(en)
if tmpl_ok or tmpl_bad:
    print(f"[模板兜底] 命中 {tmpl_ok} 条，仍未命中 {tmpl_bad} 条")
missed = still

print(f"[字典] 命中 {d_hit}/{len(items)} 条，替换 {d_cnt} 处"
      f"（字面量合并为 {n_edits} 处编辑一次写回）")
print(f"       未命中 {len(missed)} 条")
for m in missed[:40]:
    print(f"         · {m[:96]}")

src = bundle.s
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
    print("!! node --check 失败：")
    for l in [x for x in err.splitlines() if not x.startswith("[Error text truncated")][:10]:
        print("   ", l[:200])
    print(f"   现场已保留 -> {keep}")
    sys.exit(1)
os.remove(tmp)
print(f"node --check ✓（本脚本耗时 {time.perf_counter()-T0:.2f}s）")

open(BUNDLE, "w", encoding="utf-8", newline="").write(src)
print(f"已写入 {BUNDLE}")
