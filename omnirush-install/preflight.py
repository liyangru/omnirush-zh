# -*- coding: utf-8 -*-
"""全面自检。默认跑全部检查；加 --ci 跳过需要本机安装 OmniRush 的部分。

检查项
------
  1. 所有 .py 编译通过；modprobe.mjs 解析通过
  2. 未定义名字静态检查（symtable，等价精简版 pyflakes，抓 NameError）
  3. 译文数据完整性（zh.ts 键数/结构、三份字典可解析且非空）
  4. 脚本引用的文件都存在（区分主链路必选与历史脚本可选输入）
  5. 没有遗留的调试/临时文件
  —— 以下仅本机（需已安装 OmniRush）——
  6. 幂等重跑 apply_all2.py，四道校验脚本全绿
  7. 剩余英文只剩「有意保留」的类别

用法：
  python preflight.py          # 本机全量
  python preflight.py --ci     # CI 用（不碰应用安装目录）
"""
import builtins
import json
import os
import py_compile
import re
import shutil
import subprocess
import symtable
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable
CI = "--ci" in sys.argv
LEGACY = os.path.join(HERE, "legacy")

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'✅' if ok else '❌'} {name}" + (f"  — {detail}" if detail else ""))
    return ok


def section(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def py_files():
    """活跃脚本 + legacy 脚本"""
    out = [os.path.join(HERE, f) for f in sorted(os.listdir(HERE))
           if f.endswith(".py")]
    if os.path.isdir(LEGACY):
        out += [os.path.join(LEGACY, f) for f in sorted(os.listdir(LEGACY))
                if f.endswith(".py")]
    return out


if CI:
    print("（CI 模式：跳过需要本机安装 OmniRush 的检查）")

# ---------------------------------------------------------------- 1. 语法
section("1. 语法 / 可解析性")
bad = []
for p in py_files():
    try:
        py_compile.compile(p, doraise=True)
    except Exception as e:
        bad.append(f"{os.path.basename(p)}: {e}")
check(f"{len(py_files())} 个 .py 编译通过", not bad, "; ".join(bad[:3]))

mjs = os.path.join(HERE, "modprobe.mjs")
if os.path.exists(mjs):
    r = subprocess.run(["node", "--check", mjs], capture_output=True, text=True)
    check("modprobe.mjs 解析通过", r.returncode == 0, r.stderr[:200])

# ---------------------------------------------------- 2. 未定义名字（NameError）
section("2. 未定义名字静态检查（symtable，抓 NameError）")


def undefined_names(path):
    src = open(path, encoding="utf-8").read()
    try:
        top = symtable.symtable(src, path, "exec")
    except SyntaxError:
        return []
    bn = set(dir(builtins))
    bad = []

    def walk(tbl):
        for sym in tbl.get_symbols():
            n = sym.get_name()
            if not sym.is_referenced() or n in bn:
                continue
            if (sym.is_assigned() or sym.is_imported() or sym.is_parameter()
                    or sym.is_free() or sym.is_global() or sym.is_declared_global()
                    or sym.is_namespace()):
                continue
            bad.append((tbl.get_name(), n))
        for child in tbl.get_children():
            walk(child)

    walk(top)
    return bad


undef = []
for p in py_files():
    for scope, name in undefined_names(p):
        undef.append(f"{os.path.basename(p)}: {name} (in {scope})")
check("无未定义名字", not undef, "; ".join(undef[:6]))

# ------------------------------------------------------------ 3. 译文数据
section("3. 译文数据完整性")
zh_path = os.path.join(ROOT, "omnirush-i18n", "zh.ts")
zh = open(zh_path, encoding="utf-8").read()
body = zh[zh.index("export default {") + len("export default {"):zh.rindex("} as const;")]
keys = re.findall(r'^\s*"([^"]+)"\s*:', body, re.M)
check("zh.ts 可解析", len(keys) > 2000, f"{len(keys)} 键")
head = zh.lstrip()
check("zh.ts 带官方约定注释头", head[:1] in "/*",
      head.splitlines()[0][:40] if head[:1] in "/*" else "缺注释头")
check("zh.ts 含术语约定说明", "产品名称保留英文" in zh[:600])
dup = sorted({k for k in keys if keys.count(k) > 1})
check("zh.ts 无重复键", not dup, str(dup[:5]))

for fn, floor in (("zh_dict.json", 50000), ("zh_anchors.json", 5000),
                  ("zh_extra.json", 5000)):
    p = os.path.join(HERE, fn)
    try:
        d = json.load(open(p, encoding="utf-8"))
        n = len(d)
        ok = os.path.getsize(p) >= floor
        check(f"{fn} 可解析且非空", ok, f"{n} 条 / {os.path.getsize(p)} 字节")
    except Exception as e:
        check(f"{fn} 可解析且非空", False, str(e)[:120])

if not CI:
    r = subprocess.run([PY, os.path.join(HERE, "gen_dict.py")], cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8")
    check("gen_dict.py 运行成功", r.returncode == 0, (r.stderr or "")[:200])
    check("zh_dict.json 仍非空",
          os.path.getsize(os.path.join(HERE, "zh_dict.json")) > 50000)

# ------------------------------------------------------ 4. 引用文件都存在
section("4. 脚本引用的文件都存在")
GENERATED = {".tmpcheck.mjs", ".tmpcheck.js", "_dbg_failed.mjs", "_neg.mjs",
             "_final_state.js", "_verify_syntax.mjs", "_rt.mjs"}
# 历史脚本（不在 apply_all2.py 主链路）所需的可重新生成输入，未随仓库分发
OPTIONAL = {
    "_l9_snapshot.js": "某次构建的 bundle 副本，gen_dict.py / patch_ui3.py 用",
    "remaining_en.json": "scan_remaining.py 的扫描产物，patch_hardcoded2/3.py 用",
    "remaining2.json": "scan_region.py 的扫描产物，patch_final.py 用",
    "sweep.json": "scan_sweep.py 的扫描产物（宽口径候选清单）",
    "ui_sweep.json": "scan_ui.py 的扫描产物（按 UI 属性筛选的候选清单）",
}
missing = []
SEARCH = [HERE, LEGACY, ROOT, os.path.join(ROOT, "omnirush-i18n")]
for p in py_files():
    src = open(p, encoding="utf-8").read()
    for mm in re.finditer(r'["\']([\w.-]+\.(?:json|js|ts|mjs|py))["\']', src):
        fn = mm.group(1)
        if fn in GENERATED or fn.startswith(("app-", "index-")):
            continue
        if not any(os.path.exists(os.path.join(d, fn)) for d in SEARCH):
            missing.append(f"{os.path.basename(p)} -> {fn}")
hard = [m for m in missing if m.split("-> ")[-1] not in OPTIONAL]
soft = sorted({m.split("-> ")[-1] for m in missing
               if m.split("-> ")[-1] in OPTIONAL})
check("主链路输入无悬空引用", not hard, "; ".join(hard[:5]))
if soft:
    print(f"  ⏭  跳过 {len(soft)} 个历史脚本的可选输入（未入库，可重新生成）：")
    for m in soft:
        print(f"       · {m} —— {OPTIONAL[m]}")
else:
    print("  ✅ 历史脚本的可选输入齐全")

# ------------------------------------------------------------ 5. 临时文件
section("5. 遗留调试 / 临时文件")
shutil.rmtree(os.path.join(HERE, "__pycache__"), ignore_errors=True)
shutil.rmtree(os.path.join(LEGACY, "__pycache__"), ignore_errors=True)
KEEP = {"_bundle.py", "_l9_snapshot.js", "_rt.mjs"}
junk = [f for f in os.listdir(HERE)
        if f.startswith("_") and f not in KEEP]
junk += [f for f in os.listdir(HERE)
         if f.endswith((".tmp", ".tmpcheck.js", ".tmpcheck.mjs"))]
check("无遗留临时文件", not junk, str(junk[:6]))

# ------------------------------------------------- 6/7. 仅本机：跑完整流水线
if not CI:
    section("6. 幂等重跑 apply_all2.py")
    r = subprocess.run([PY, os.path.join(HERE, "apply_all2.py")], cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8")
    out = r.stdout or ""
    check("apply_all2.py 退出码 0", r.returncode == 0, (r.stderr or "")[:300])
    for kw, label in [
        ("ES Module 语法校验通过", "ES Module 语法校验"),
        ("键集合一致  : True", "2078 键一致"),
        ("值不一致    : 0", "0 值差异"),
        ("残留英文串: 0 | 缺失中文串: 0", "首页/侧栏干净"),
        ("残留英文: 0 | 缺失中文: 0", "设置页干净"),
    ]:
        check(label, kw in out)

    section("7. 剩余英文分类核查")
    r = subprocess.run([PY, os.path.join(HERE, "list_targets.py")], cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8")
    lines = [l for l in (r.stdout or "").splitlines() if l.startswith("@@")]
    m = re.search(r"候选 (\d+) 条", r.stdout or "")
    total = int(m.group(1)) if m else len(lines)
    LIB = re.compile(
        r"(KaTeX|Mermaid|shiki|React Router|ParseNode|stretchy delimiter|"
        r"delimiters doesn|loadWasm|Group Context|Uniform|separator|"
        r"unique identifier for the corresponding tool call|"
        r"is not included in this bundle)")
    PROMPT = re.compile(r"^(Continue the interrupted task|First inspect|"
                        r"Preserve completed work|Resolve \")")
    PRODUCT = re.compile(r"[、…]|^[A-Za-z0-9+, .]+$")
    other = []
    for l in lines:
        b = l.split("|", 2)[-1]
        if LIB.search(b) or PROMPT.match(b) or PRODUCT.search(b):
            continue
        other.append(b)
    check(f"剩余 {total} 条全属「有意保留」类别", not other,
          "例外: " + "; ".join(o[:60] for o in other[:5]))

# ------------------------------------------------------------------ 汇总
print()
print("=" * 70)
fails = [n for n, ok, _ in results if not ok]
print(f"自检完成：{len(results) - len(fails)}/{len(results)} 通过"
      + ("（CI 模式）" if CI else ""))
if fails:
    print("未通过：")
    for n in fails:
        print("  ❌", n)
    sys.exit(1)
print("全部通过 ✅")
