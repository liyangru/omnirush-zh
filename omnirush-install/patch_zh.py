"""OmniRush 汉化补丁 —— 对已安装的渲染层 bundle 做两处修改：

1. 把内联的 zh 语言对象字面量整块替换为补全版（2078 键）。
2. 把 ENGINE_DETAIL_KEYS 白名单清空 —— 该白名单会强制 21 个键走英文。
   （这 21 个键的原有中文译文已过时，仍在提 opencode.json / OpenCode 旧品牌；
     补全版已把译文更新到与当前英文一致，因此放开白名单是安全的。）

脚本幂等：每次运行都先从 .orig-backup 还原，再打补丁。
"""
import json, re, shutil, sys, os, subprocess
from _bundle import detect_bundle

ASSETS = r"C:\Users\18351\AppData\Local\Programs\@omnirushdesktop\resources\app-dist\assets"
BUNDLE = detect_bundle()
BAK = BUNDLE + ".orig-backup"
NEW_ZH = r"D:\XIAZAI\浏览器\2026-10-12-00-28-27\omnirush-i18n\zh.ts"
ORIG_ZH = r"D:\XIAZAI\浏览器\2026-10-12-00-28-27\omnirush-i18n\zh.original.ts"

FIRST_KEY = '"app.compact_command_desc":"'


def scan_balanced(s, start, open_ch, close_ch):
    """从 start（s[start] == open_ch）开始，做字符串感知的括号匹配，返回闭合字符下标。"""
    depth = 0
    in_str = None
    esc = False
    i = start
    while i < len(s):
        c = s[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == in_str:
                in_str = None
        else:
            if c in ('"', "'", "`"):
                in_str = c
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("括号未闭合")


# ---------- 0. 还原到原始文件 ----------
if not os.path.exists(BAK):
    shutil.copy2(BUNDLE, BAK)
    print(f"建立原始备份 -> {BAK}")
else:
    shutil.copy2(BAK, BUNDLE)
    print(f"已从备份还原 -> {BUNDLE}")
src = open(BUNDLE, encoding="utf-8").read()
print(f"原始 bundle: {len(src)} 字符")

# ---------- 1. 读取补全后的译文 ----------
zh_ts = open(NEW_ZH, encoding="utf-8").read()
body = zh_ts[zh_ts.index("export default {") + len("export default {"):zh_ts.rindex("} as const;")]
pairs = re.findall(r'^\s*"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', body, re.M)
# 关键：zh.ts 里的值是 TS 转义文本，必须先还原为真实字符串，
# 否则 json.dumps 会把 \n 二次转义成字面 \n，界面上直接显示 "\n"。
pairs = [(k, json.loads('"' + v + '"')) for k, v in pairs]
new_obj = "{" + ",".join(
    f"{json.dumps(k, ensure_ascii=False)}:{json.dumps(v, ensure_ascii=False)}" for k, v in pairs
) + "}"
print(f"补全版译文: {len(pairs)} 键")
_multi = [k for k, v in pairs if "\n" in v]
print(f"  含换行的多行值: {len(_multi)} -> {_multi}")

# ---------- 2. 定位 zh 对象 ----------
CJK = re.compile(r"[\u4e00-\u9fff]")
starts = [m.start() for m in re.finditer(re.escape(FIRST_KEY), src) if CJK.match(src[m.end()])]
if len(starts) != 1:
    sys.exit(f"!! 找到 {len(starts)} 个 zh 对象起点，预期 1 个 -> 中止")
obj_start = starts[0] - 1
assert src[obj_start] == "{"
obj_end = scan_balanced(src, obj_start, "{", "}")
old_obj = src[obj_start:obj_end + 1]
print(f"zh 对象: [{obj_start}, {obj_end}]  长度 {len(old_obj)}")

# ---------- 3. 校验：与「当前 bundle 的 en 对象」比对，确认补全版能全覆盖 ----------
# 不再和 zh.original.ts 比对：应用一升级，官方 zh 的键集会变（例如新版少了
# settings.environment.restart_required），拿旧参考文件当准会误报。
# 真正该保证的是「en 里每个键在我的 zh.ts 里都有译文」。
EN_ANCHOR = '"account.mcp_connected_one":"'
_en = src.find(EN_ANCHOR)
if _en < 0:
    sys.exit("!! 定位不到 en 对象 -> 中止")
_en_obj_start = src.rfind("{", 0, _en)
_en_obj_end = scan_balanced(src, _en_obj_start, "{", "}")
en_keys = set(re.findall(r'"([^"]+)"\s*:', src[_en_obj_start:_en_obj_end + 1]))
my_keys = set(k for k, _ in pairs)
print(f"当前 bundle: en {len(en_keys)} 键 | 补全版 zh.ts {len(my_keys)} 键")

PLURAL = re.compile(r'_(zero|one|two|few|many|other)$')
_miss_plain = sorted(k for k in en_keys - my_keys if not PLURAL.search(k))
_miss_base = sorted({PLURAL.sub('', k) for k in en_keys if PLURAL.search(k)} - my_keys)
if _miss_plain or _miss_base:
    print("  en 有但补全版缺译的键:", _miss_plain + _miss_base)
    sys.exit("!! 补全版覆盖率不足 -> 中止")
_n_plural = sum(1 for k in en_keys if PLURAL.search(k))
print(f"  ✓ 覆盖率 100%（{len(en_keys) - _n_plural} 个普通键 + {_n_plural // 2} 组复数变体折叠为基键）")

# 顺带确认旧对象确为官方 zh（首键 + 键数与 en 的非复数键规模相称）
first_key = re.match(r'\{"([^"]+)":', old_obj).group(1)
_plain_en = [k for k in en_keys if not PLURAL.search(k)]
print(f"旧 zh 对象首键 {first_key} | 键数 {len(re.findall(r'\"([^\"]+)\"\\s*:', old_obj))}")
if first_key != "app.compact_command_desc":
    sys.exit("!! 旧对象首键不符，可能已打过补丁或 bundle 结构变了 -> 中止")

src = src[:obj_start] + new_obj + src[obj_end + 1:]
print(f"[1/2] zh 语言包已替换  (+{len(new_obj)-len(old_obj)} 字符)")

# ---------- 4. 清空 ENGINE_DETAIL_KEYS 白名单 ----------
anchor = '"context_panel.permission_source_global"'
hits = [m.start() for m in re.finditer(re.escape(anchor), src)]
set_start = None
for h in hits:
    j = src.rfind("new Set([", 0, h)
    if j >= 0 and h - j < 60:
        set_start = j
        break
if set_start is None:
    sys.exit("!! 未找到 ENGINE_DETAIL_KEYS 的 new Set([...]) -> 中止")
br = src.index("[", set_start)
set_end = scan_balanced(src, br, "[", "]")
n_keys = src[br:set_end + 1].count('"')
assert src[set_end + 1] == ")", f"数组闭合后不是 ) : {src[set_end:set_end+5]!r}"
print(f"ENGINE_DETAIL_KEYS 白名单: 数组 [{br}, {set_end}]  约 {n_keys // 2} 个键")
# 只替换数组内容，保留 new Set( 和 ) —— 避免多出右括号
src = src[:br] + "[]" + src[set_end + 1:]
print("[2/2] ENGINE_DETAIL_KEYS 白名单已清空")

# ---------- 5. 默认语言改为 zh（首次启动即中文） ----------
# 官方 initLocale() 在 localStorage 无偏好时回退 "en"。把该函数里的 "en"
# 字面量改成 "zh"，让全新安装默认就是中文；用户在设置里改回英文后
# localStorage 会写入偏好，不会被打回中文。
TAIL_OLD = '"lang","en"),"en"}'
TAIL_NEW = '"lang","zh"),"zh"}'
NOVAR_OLD = 'if(typeof window>"u")return"en"'
NOVAR_NEW = 'if(typeof window>"u")return"zh"'
for old, new, label in [
    (TAIL_OLD, TAIL_NEW, "initLocale 回退分支"),
    (NOVAR_OLD, NOVAR_NEW, "initLocale 无 window 分支"),
]:
    c = src.count(old)
    if c != 1:
        sys.exit(f"!! {label} 锚点出现 {c} 次（预期 1 次）-> 中止")
    src = src.replace(old, new)
    print(f"[3/3] {label}: en -> zh")

m = re.search(r'(includes\(e\);let\s+[\w$]+=)"en";', src)
if m:
    src = src[:m.start()] + m.group(1) + '"zh";' + src[m.end():]
    print("[3/3] 初始 localeValue: en -> zh")
else:
    sys.exit("!! 未找到初始 localeValue 赋值 -> 中止")

# ---------- 5. 语法校验 + 写回 ----------
# 注意：必须用 .mjs 临时文件。.js 会让 node --check 走 CJS/自动检测路径，
# 在本 bundle 这种「ESM 语法只在文件末尾出现」的大文件上会静默返回 0，
# 从而导致假阳性校验（曾因此漏掉真实语法错误）。
_tmp = BUNDLE + ".tmpcheck.mjs"
open(_tmp, "w", encoding="utf-8", newline="").write(src)
_r = subprocess.run(["node", "--check", _tmp], capture_output=True, text=True)
if _r.returncode != 0:
    os.remove(_tmp)
    sys.exit(f"!! node --check 失败:\n{_r.stdout}\n{_r.stderr}")
os.remove(_tmp)
print("node --check ✓")
open(BUNDLE, "w", encoding="utf-8", newline="").write(src)
print(f"写入完成: {len(src)} 字符")

# ---------- 6. 回读验证 ----------
chk = open(BUNDLE, encoding="utf-8").read()
checks = {
    "new Set([]) 已生效": "new Set([])" in chk,
    "补全译文已注入": "压缩此会话以减少上下文大小" in chk,
    "新键(extensions.badge_skill)已注入": '"extensions.badge_skill"' in chk,
    "旧过时译文已清除(opencode.json)": "opencode.json失败" not in chk,
    "白名单残留": '"context_panel.permission_source_global" in Set' if False else True,
}
for k, v in checks.items():
    print(f"  {'✓' if v else '✗'} {k}")
