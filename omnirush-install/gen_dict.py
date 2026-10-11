# -*- coding: utf-8 -*-
"""汇总各层译文，生成「英文 -> 中文」内容字典 zh_dict.json。

为什么需要它
------------
应用自动更新会重写 app-dist/，bundle 文件名与全部字节偏移都变，
原来依赖偏移量的替换（hardcoded_ui.json / remaining*.json / _l9_snapshot.js）全部作废。
所以这里把所有已知译文汇总成**与偏移无关**的字典，只要字符串本身没变就能用。

来源
----
  patch_hardcoded.py   TRANS / ANCHORS
  patch_hardcoded2.py  T
  patch_hardcoded3.py  T3
  patch_settings.py    A（锚点）
  patch_final.py       T
  patch_ext.py         ANCHORS
  patch_ui.py          T / RAW
  patch_ui2.py         T / RAW
  patch_ui3.py         T（偏移+译文，英文原文从 _l9_snapshot.js 反推）
  手工补充            截图里新发现的漏译文案

锚点是复合代码片段（如 'children:"Audit trail"' -> 'children:"审计日志"'），
这里按顺序对齐其中的引号片段，取出 (英文, 中文) 对。
"""
import ast
import sys
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LEGACY = os.path.join(HERE, "legacy")   # 历史分层补丁脚本（译文表的来源）
CJK = re.compile(r"[\u4e00-\u9fff]")
QLIT = re.compile(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'|`((?:[^`\\]|\\.)*)`')


def top_assign(path, var):
    """用 AST 取出脚本顶层某个变量的字面量（不执行脚本）"""
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id == var:
                    return ast.literal_eval(node.value)
    return None


def quoted(s):
    """取出字符串里所有引号片段的内容"""
    out = []
    for m in QLIT.finditer(s):
        out.append(m.group(1) if m.group(1) is not None else (
            m.group(2) if m.group(2) is not None else m.group(3)))
    return out


def pairs_from_anchor(old, new):
    """对齐锚点新旧片段中的引号内容，返回 [(英文, 中文), ...]"""
    o, n = quoted(old), quoted(new)
    if len(o) != len(n):
        return []
    res = []
    for a, b in zip(o, n):
        if not a or not b or a == b:
            continue
        if CJK.search(a):          # 原文侧不应含中文
            continue
        if not re.search(r"[A-Za-z]{2}", a):
            continue
        # 片段必须是纯文案，不能是代码
        if re.search(r"[{}<>()\[\];=]|=>", a):
            continue
        res.append((a, b))
    return res


def clean_key(s):
    return len(s) >= 3 and not CJK.search(s)


D = {}
ANCHOR_LIST = []   # [(old_fragment, new_fragment)] 优先按整段代码替换
ANCHOR_KEYS = set()  # 已被锚点覆盖的英文字符串，平铺字典里跳过
stat = {}


def add(pairs, tag):
    n = 0
    for en, zh in pairs:
        if not clean_key(en):
            continue
        if en in D and D[en] != zh:
            stat.setdefault("conflict", []).append((en, D[en], zh))
        D[en] = zh
        n += 1
    stat[tag] = n


def add_anchors(anchors, tag):
    """复合代码锚点：整段替换优先，同时登记其英文字符串键"""
    n = 0
    for old, new in anchors:
        ANCHOR_LIST.append((old, new))
        for k, _ in pairs_from_anchor(old, new):
            ANCHOR_KEYS.add(k)
        n += 1
    stat[tag] = n


# ---------- 0. 锚点 / RAW 先入字典（通用译文后入会覆盖它们，锚点仅作整段优先替换）----------
for script, var in [("patch_hardcoded.py", "ANCHORS"),
                    ("patch_settings.py", "A"),
                    ("patch_ext.py", "ANCHORS")]:
    anchors = top_assign(os.path.join(LEGACY, script), var) or []
    add_anchors([(a[0], a[1]) for a in anchors], f"{script}:{var}")
for script, var in [("patch_ui.py", "RAW"), ("patch_ui2.py", "RAW")]:
    raws = top_assign(os.path.join(LEGACY, script), var) or []
    add_anchors([(a[0], a[1]) for a in raws], f"{script}:{var}")

# ---------- 1. 字典型 / 二元组型表 ----------
for script, var in [("patch_hardcoded.py", "TRANS"),
                    ("patch_hardcoded2.py", "T"),
                    ("patch_hardcoded3.py", "T3"),
                    ("patch_final.py", "T")]:
    tbl = top_assign(os.path.join(LEGACY, script), var)
    if not tbl:
        continue
    add(list(tbl.items()) if isinstance(tbl, dict) else tbl, f"{script}:{var}")

# ---------- 2. (内容, 译文, 预期次数) 列表 ----------
# 注意顺序：锚点/RAW 的上下文相关译文先入字典，随后被下面的通用译文覆盖，
# 保证「锚点整段替换优先、通用译文兜底」。
for script, var in [("patch_ui.py", "T"), ("patch_ui2.py", "T")]:
    tbl = top_assign(os.path.join(LEGACY, script), var) or []
    add([(a, b) for a, b, _ in tbl], f"{script}:{var}")

# ---------- 3. 第 10 层：从快照反推英文原文 ----------
# 快照是某次构建的本地副本，未随仓库分发（体积大且属应用专有代码）。
# 缺失时跳过这一步：zh_dict.json 里已有的对应条目不受影响，只是无法重新反推。
SNAP = os.path.join(HERE, "_l9_snapshot.js")
if os.path.exists(SNAP):
    snap = open(SNAP, encoding="utf-8").read()
else:
    snap = None
    print("  ! 未找到 _l9_snapshot.js —— 无法反推第 10 层的 471 条英文原文。")
    print("    为免覆盖已提交的 zh_dict.json，本次不写入任何文件。")
    print("    如需完整重建：把某一层打完的 bundle 存为 _l9_snapshot.js 后重跑。")
    sys.exit(0)


def extract(s, i):
    """返回字面量结束定界符下标；支持 ${} 嵌套与内层模板"""
    d = s[i]
    j = i + 1
    if d == "`":
        depth = 0
        while j < len(s):
            c = s[j]
            if c == "\\":
                j += 2
                continue
            if c == "$" and j + 1 < len(s) and s[j + 1] == "{":
                depth += 1
                j += 2
                continue
            if c == "}" and depth > 0:
                depth -= 1
                j += 1
                continue
            if c == "`" and depth == 0:
                return j
            j += 1
        return -1
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == d:
            return j
        j += 1
    return -1


t10 = top_assign(os.path.join(LEGACY, "patch_ui3.py"), "T") or []
out, miss = [], 0
for off, trans in (t10 if snap is not None else []):
    e = extract(snap, off)
    if e < 0:
        miss += 1
        continue
    en = snap[off + 1:e]
    # 剥掉译文自带的定界符
    if en.startswith("`") and en.endswith("`"):
        en = en[1:-1]
    out.append((en, trans))
add(out, "patch_ui3.py:T(反推)")
if miss:
    print(f"  (patch_ui3 有 {miss} 条无法从快照反推)")

# ---------- 6. 截图新发现的漏译 ----------
NEW = [
    ("Sub-agents are the helpers the main agent starts with the task tool, at every nesting layer. The main agent keeps its own model and effort. If the picked model is not available to your account or omnirush.ai refuses it, sub-agents run on the main agent's model and the session says so.",
     "子智能体是主智能体通过 task 工具在各层级启动的助手。主智能体保留自己的模型和投入强度。如果所选模型对你的账号不可用，或 omnirush.ai 拒绝使用它，子智能体将运行在主智能体的模型上，会话中会说明这一点。"),
    ('How hard sub-agents think. "Same as main agent" uses the main agent\'s effort, mapped to the nearest level the sub-agent model offers.',
     '子智能体的思考强度。“与主智能体相同”使用主智能体的投入强度，映射到子智能体模型支持的最接近级别。'),
    ("Same as main agent", "与主智能体相同"),
    ("Privacy", "隐私"),
    ('`Voice is transcribed by our cloud speech provider. ${e?`omnirush.ai doesn\'t store your audio; the provider keeps a copy for up to ${e} days.`:"omnirush.ai doesn\'t store your audio."} Nothing is saved on this computer, and only the text you send becomes part of your prompt.`',
     '`语音由我们的云端语音提供商转写。${e?`omnirush.ai 不存储你的音频；提供商会保留副本最多 ${e} 天。`:"omnirush.ai 不存储你的音频。"} 本机不保存任何内容，只有你发送的文本会成为提示词的一部分。`'),
]
NEW_out = []
for en, zh in NEW:
    if en.startswith("`") and en.endswith("`") and len(en) > 2:
        NEW_out.append((en[1:-1], zh[1:-1] if zh.startswith("`") and zh.endswith("`") else zh))
    else:
        NEW_out.append((en, zh))
add(NEW_out, "手工补充(截图漏译)")

# ---------- 输出 ----------
print("\n=== 各来源条数 ===")
for k, v in stat.items():
    if k != "conflict":
        print(f"  {k:34s} {v}")
if stat.get("conflict"):
    print("\n=== 译文冲突（保留后者，需人工确认）===")
    for en, a, b in stat["conflict"]:
        print(f"  {en[:60]!r}\n     A={a[:50]!r}\n     B={b[:50]!r}")

out_path = os.path.join(HERE, "zh_dict.json")
json.dump(D, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
anchor_path = os.path.join(HERE, "zh_anchors.json")
json.dump(ANCHOR_LIST, open(anchor_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n平铺字典 {len(D)} 条 -> {out_path}")
print(f"复合锚点 {len(ANCHOR_LIST)} 条 -> {anchor_path}")
