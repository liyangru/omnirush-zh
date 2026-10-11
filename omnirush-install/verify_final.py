"""终检：把 bundle 运行时真正持有的 zh 对象抽出来，与「期望值」逐键比对。

期望值来源：
  - 我新翻译的键  -> trans1..4.json（JSON 解析即真实字符串）
  - 沿用官方译文  -> zh.original.ts（还原 TS 转义）
比对用 Node 执行 bundle 里的对象字面量，拿到运行时真实字符串。
"""
import json, re, subprocess, os, shutil
from _bundle import detect_bundle

BUNDLE = detect_bundle()
HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "omnirush-i18n")
def _find_node():
    """优先用 PATH 里的 node，找不到再回退到常见安装位置"""
    exe = shutil.which("node")
    if exe:
        return exe
    for cand in ['C:\\Users\\18351\\.workbuddy-ai\\binaries\\node\\versions\\22.22.2-6\\node.exe']:
        if os.path.exists(cand):
            return cand
    return "node"


NODE = _find_node()

PLURAL = ("zero", "one", "two", "few", "many", "other")
PRE = re.compile(r"_(?:" + "|".join(PLURAL) + r")$")


def parse_ts(fn):
    """解析 locale .ts，返回 真实字符串 的 key->value。"""
    t = open(fn, encoding="utf-8").read()
    b = t[t.index("export default {"):]
    out = {}
    for m in re.finditer(r'^\s*"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', b, re.M):
        out[m.group(1)] = json.loads('"' + m.group(2) + '"')
    return out


en = parse_ts(os.path.join(I18N, "en.ts"))
old = parse_ts(os.path.join(I18N, "zh.original.ts"))
mine = {}
for i in (1, 2, 3, 4):
    mine.update(json.load(open(os.path.join(I18N, f"trans{i}.json"), encoding="utf-8")))

# 期望的最终 zh 键值（与 merge.py 同逻辑）
plural_bases = {PRE.sub("", k) for k in en if PRE.search(k)}
expected = {}
used = set()
for k in en:
    if k in used:
        continue
    if PRE.search(k):
        base = PRE.sub("", k)
        for s in PLURAL:
            used.add(f"{base}_{s}")
        expected[base] = mine.get(base, old.get(base, en[k]))
        continue
    used.add(k)
    expected[k] = mine.get(k, old.get(k, en[k]))

# ---- 用 Node 从 bundle 抽运行时对象 ----
src = open(BUNDLE, encoding="utf-8").read()
i = src.find('"account.mcp_connected"')
z0 = src.rfind("{", 0, i)
z1 = src.index("},B8e=", z0) + 1
raw = src[z0:z1]
open(os.path.join(HERE, "_rt.mjs"), "w", encoding="utf-8").write(
    "const o=" + raw + ";\nconsole.log(JSON.stringify(o));\n")
out = subprocess.run([NODE, os.path.join(HERE, "_rt.mjs")], capture_output=True, text=True,
                     encoding="utf-8", cwd=HERE)
if out.returncode != 0:
    raise SystemExit("Node 解析 bundle 失败:\n" + out.stderr[:2000])
rt = json.loads(out.stdout)

print("=== bundle 运行时 zh 对象 vs 期望值 ===")
print(f"bundle 键数 : {len(rt)}")
print(f"期望键数    : {len(expected)}")
print(f"键集合一致  : {set(rt) == set(expected)}")
missing = sorted(set(expected) - set(rt))
extra = sorted(set(rt) - set(expected))
if missing:
    print("  缺失:", missing[:10])
if extra:
    print("  多余:", extra[:10])
diff = [k for k in expected if rt.get(k) != expected[k]]
print(f"值不一致    : {len(diff)}")
for k in diff[:10]:
    print(f"  ✗ {k}\n      期望 {expected[k]!r}\n      实际 {rt.get(k)!r}")

print()
print("=== 多行值专项（最易出转义 bug）===")
multi = [k for k, v in expected.items() if "\n" in v]
for k in multi:
    ok = rt.get(k) == expected[k]
    print(f"  {'✓' if ok else '✗'} {k}  (换行数 {expected[k].count(chr(10))})")
    if not ok:
        print("      期望:", repr(expected[k]))
        print("      实际:", repr(rt.get(k)))

print()
print("=== 反斜杠专项：确认无字面 \\n 残留 ===")
bad = [k for k, v in rt.items() if "\\n" in v or "\\t" in v]
print(f"  含字面反斜杠转义的键: {len(bad)} {bad[:5]}")

ok_all = set(rt) == set(expected) and not diff
print()
print("结论:", "✅ bundle 内中文数据与期望完全一致，无转义问题" if ok_all else "❌ 仍存在差异")
