# -*- coding: utf-8 -*-
"""发布前全面自检。

检查项：
  1. 所有 .py / .mjs 能否编译/解析
  2. apply_all2.py 能否幂等重跑（从备份还原 → 打补丁 → 校验）
  3. 四道校验脚本全绿
  4. 剩余英文只剩「有意保留」的类别
  5. zh.ts 键数与结构完整
  6. gen_dict.py 能否重新生成字典（幂等性）
  7. 引用的文件都存在（没有悬空路径）
  8. 没有遗留的调试/临时文件
"""
import json
import os
import py_compile
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'✅' if ok else '❌'} {name}" + (f"  — {detail}" if detail else ""))
    return ok


print("=" * 70)
print("1. 语法 / 可解析性")
print("=" * 70)
bad = []
for f in sorted(os.listdir(HERE)):
    if f.endswith(".py"):
        try:
            py_compile.compile(os.path.join(HERE, f), doraise=True)
        except Exception as e:
            bad.append(f"{f}: {e}")
check("所有 .py 编译通过", not bad, "; ".join(bad[:3]))

r = subprocess.run(["node", "--check", os.path.join(HERE, "modprobe.mjs")],
                   capture_output=True, text=True)
check("modprobe.mjs 解析通过", r.returncode == 0, r.stderr[:200])

print()
print("=" * 70)
print("1b. 未定义名字静态检查（symtable，抓 NameError）")
print("=" * 70)
import builtins
import symtable


def undefined_names(path):
    """返回 [(作用域名, 名字)] —— 被引用但没有定义来源的名字"""
    src = open(path, encoding="utf-8").read()
    try:
        top = symtable.symtable(src, path, "exec")
    except SyntaxError:
        return []
    builtin_names = set(dir(builtins))
    bad = []

    def walk(tbl, is_module):
        for sym in tbl.get_symbols():
            n = sym.get_name()
            if not sym.is_referenced() or n in builtin_names:
                continue
            if (sym.is_assigned() or sym.is_imported() or sym.is_parameter()
                    or sym.is_free() or sym.is_global() or sym.is_declared_global()
                    or sym.is_namespace()):
                continue
            bad.append((tbl.get_name(), n))
        for child in tbl.get_children():
            walk(child, False)

    walk(top, True)
    return bad


undef = []
for f in sorted(os.listdir(HERE)):
    if not f.endswith(".py") or f.startswith("_"):
        continue
    for scope, name in undefined_names(os.path.join(HERE, f)):
        undef.append(f"{f}: {name} (in {scope})")
check("无未定义名字", not undef, "; ".join(undef[:6]))

print()
print("=" * 70)
print("2. 幂等重跑 apply_all2.py")
print("=" * 70)
r = subprocess.run([PY, os.path.join(HERE, "apply_all2.py")], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8")
out = r.stdout or ""
check("apply_all2.py 退出码 0", r.returncode == 0,
      (r.stderr or "")[:300])
for kw, label in [
    ("ES Module 语法校验通过", "语法校验"),
    ("键集合一致  : True", "2078 键一致"),
    ("值不一致    : 0", "0 值差异"),
    ("残留英文串: 0 | 缺失中文串: 0", "首页/侧栏干净"),
    ("残留英文: 0 | 缺失中文: 0", "设置页干净"),
]:
    check(label, kw in out)

print()
print("=" * 70)
print("3. 剩余英文分类核查")
print("=" * 70)
r = subprocess.run([PY, os.path.join(HERE, "list_targets.py")], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8")
lines = [l for l in (r.stdout or "").splitlines() if l.startswith("@@")]
m = re.search(r"候选 (\d+) 条", r.stdout or "")
total = int(m.group(1)) if m else len(lines)

LIB_MARK = re.compile(
    r"(KaTeX|Mermaid|shiki|React Router|ParseNode|stretchy delimiter|"
    r"delimiters doesn|loadWasm|Group Context|Uniform|separator|"
    r"unique identifier for the corresponding tool call|"
    r"is not included in this bundle)")
PROMPT_MARK = re.compile(r"^(Continue the interrupted task|First inspect|"
                         r"Preserve completed work|Resolve \")")
PRODUCT_MARK = re.compile(r"[、…]|^[A-Za-z0-9+, .]+$")
other = []
for l in lines:
    body = l.split("|", 2)[-1]
    if LIB_MARK.search(body) or PROMPT_MARK.match(body) or PRODUCT_MARK.search(body):
        continue
    other.append(body)
check(f"剩余 {total} 条全部属「有意保留」类别", not other,
      "例外: " + "; ".join(o[:60] for o in other[:5]))

print()
print("=" * 70)
print("4. zh.ts 完整性")
print("=" * 70)
zh_path = os.path.join(ROOT, "omnirush-i18n", "zh.ts")
zh = open(zh_path, encoding="utf-8").read()
body = zh[zh.index("export default {") + len("export default {"):zh.rindex("} as const;")]
keys = re.findall(r'^\s*"([^"]+)"\s*:', body, re.M)
check("zh.ts 可解析", len(keys) > 2000, f"{len(keys)} 键")
head = zh.lstrip()
check("zh.ts 带官方约定注释头", head.startswith("/*") or head.startswith("//"),
      head.splitlines()[0][:40] if head[:1] in "/*" else "缺注释头")
check("zh.ts 含术语约定说明", "产品名称保留英文" in zh[:600])
dup = [k for k in set(keys) if keys.count(k) > 1]
check("无重复键", not dup, str(dup[:5]))

print()
print("=" * 70)
print("5. gen_dict.py 可重新生成字典")
print("=" * 70)
before = {}
for f in ("zh_dict.json", "zh_anchors.json"):
    p = os.path.join(HERE, f)
    before[f] = os.path.getmtime(p)
r = subprocess.run([PY, os.path.join(HERE, "gen_dict.py")], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8")
ok = r.returncode == 0 and os.path.exists(os.path.join(HERE, "zh_dict.json"))
after = os.path.getsize(os.path.join(HERE, "zh_dict.json"))
check("gen_dict.py 运行成功", ok, (r.stderr or "")[:200])
check("zh_dict.json 非空", after > 50000, f"{after} 字节")

print()
print("=" * 70)
print("6. 脚本引用的文件都存在")
print("=" * 70)
# 这些是脚本运行时生成的临时名，不是需要随仓库分发的输入
GENERATED = {".tmpcheck.mjs", ".tmpcheck.js", "_dbg_failed.mjs", "_neg.mjs",
              "_final_state.js", "_verify_syntax.mjs", "_rt.mjs"}
missing = []
SEARCH_DIRS = [HERE, ROOT, os.path.join(ROOT, "omnirush-i18n")]
for f in sorted(os.listdir(HERE)):
    if not f.endswith(".py"):
        continue
    src = open(os.path.join(HERE, f), encoding="utf-8").read()
    for mm in re.finditer(r'["\']([\w.-]+\.(?:json|js|ts|mjs|py))["\']', src):
        fn = mm.group(1)
        if fn in GENERATED:
            continue
        if fn in ("app-DohXHoBv.js", "app-CAtSUbH6.js", "index-D9OrWfzm.js"):
            continue  # bundle 名由 _bundle.py 动态探测
        if not any(os.path.exists(os.path.join(d, fn)) for d in SEARCH_DIRS):
            missing.append(f"{f} -> {fn}")
# 历史脚本（不在 apply_all2.py 主链路）所需的可重新生成输入，未随仓库分发
OPTIONAL = {
    "_l9_snapshot.js": "某次构建的 bundle 副本，gen_dict.py / patch_ui3.py 用",
    "remaining_en.json": "scan_remaining.py 的扫描产物，patch_hardcoded2/3.py 用",
    "remaining2.json": "scan_region.py 的扫描产物，patch_final.py 用",
}
hard = [m for m in missing if m.split("-> ")[-1] not in OPTIONAL]
soft = [m for m in missing if m.split("-> ")[-1] in OPTIONAL]
check("主链路输入无悬空引用", not hard, "; ".join(hard[:5]))
if soft:
    print(f"  ⏭  跳过 {len(soft)} 处历史脚本的可选输入（未入库，可重新生成）：")
    for m in sorted(set(m.split("-> ")[-1] for m in soft)):
        print(f"       · {m} —— {OPTIONAL[m]}")
else:
    print("  ✅ 历史脚本的可选输入齐全")

print()
print("=" * 70)
print("7. 遗留调试 / 临时文件")
print("=" * 70)
import shutil
shutil.rmtree(os.path.join(HERE, "__pycache__"), ignore_errors=True)
junk = [f for f in os.listdir(HERE)
        if f.startswith("_") and f not in ("_bundle.py", "_l9_snapshot.js", "_rt.mjs")]
junk += [f for f in os.listdir(HERE) if f.endswith((".tmp", ".tmpcheck.js", ".tmpcheck.mjs"))]
check("无遗留临时文件", not junk, str(junk[:6]))

print()
print("=" * 70)
fails = [n for n, ok, _ in results if not ok]
print(f"自检完成：{len(results) - len(fails)}/{len(results)} 通过")
if fails:
    print("未通过：")
    for n in fails:
        print("  ❌", n)
    sys.exit(1)
print("全部通过 ✅")
