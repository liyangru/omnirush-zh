import re, json, collections

PLURAL = ("zero", "one", "two", "few", "many", "other")
PLURAL_RE = re.compile(r"_(?:" + "|".join(PLURAL) + r")$")

def parse(fn):
    s = open(fn, encoding="utf-8").read()
    body = s[s.index("export default {"):]
    out = {}
    order = []
    for m in re.finditer(r'^\s*"([^"]+)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', body, re.M):
        k = m.group(1)
        if k not in out:
            order.append(k)
        # 关键：把 TS 转义文本还原为真实字符串，避免后续 json.dumps 二次转义
        out[k] = json.loads('"' + m.group(2) + '"')
    return out, order

en, en_order = parse("en.ts")
zh_old, _ = parse("zh.original.ts")

mine = {}
for i in (1, 2, 3, 4):
    mine.update(json.load(open(f"trans{i}.json", encoding="utf-8")))

# 找出 en 中的复数基键：任何带 CLDR 复数后缀的键都算
plural_bases = {PLURAL_RE.sub("", k) for k in en if PLURAL_RE.search(k)}
# 基键本身也是独立键的情况（折叠时不能丢）
bare_collisions = sorted(b for b in plural_bases if b in en)
if bare_collisions:
    print("!! 基键与独立键同名，需人工确认:", bare_collisions)

result = {}          # 最终 zh key -> value
used = set()         # 已消耗的 en 键
for k in en_order:
    if k in used:
        continue
    if PLURAL_RE.search(k):
        base = PLURAL_RE.sub("", k)
        for suffix in PLURAL:
            used.add(f"{base}_{suffix}")
        if base in mine:
            result[base] = mine[base]
        elif base in zh_old:
            result[base] = zh_old[base]
        else:
            result[base] = en[k]
        continue
    used.add(k)
    if k in mine:
        result[k] = mine[k]
    elif k in zh_old:
        result[k] = zh_old[k]
    else:
        result[k] = en[k]

# 记录统计
import io
report = []
new_translated = [k for k in mine if k in result and mine[k] == result[k]]
kept_old = [k for k in result if k not in mine and k in zh_old]
fallback_en = [k for k in result if k not in mine and k not in zh_old]
report.append(f"最终键数        : {len(result)}")
report.append(f"en 键数         : {len(en)}")
report.append(f"en 复数变体折叠 : {len(en) - len(used)} 个 -> {len(plural_bases)} 个基键")
report.append(f"本次新翻译      : {len(new_translated)}")
report.append(f"沿用原有译文    : {len(kept_old)}")
report.append(f"回退英文(未译)  : {len(fallback_en)}")
if fallback_en:
    report.append("  回退项: " + ", ".join(fallback_en[:30]))
orphans = [k for k in zh_old if k not in en and k not in result]
report.append(f"原有孤立键(未保留): {len(orphans)} {orphans}")

# 覆盖率：en 的每个键是否都能解析到中文
missing = []
for k in en_order:
    if PLURAL_RE.search(k):
        base = PLURAL_RE.sub("", k)
        if base in plural_bases:
            if base not in result:
                missing.append(base)
    elif k not in result:
        missing.append(k)
report.append(f"未覆盖 en 键    : {len(missing)} {missing[:20]}")

# 输出 zh.ts
header = '''/**
 * 中文（简体）翻译
 * 产品名称保留英文：OpenCode、OpenPackage、omnirush.ai
 * Skills：标题用"Skills（技能）"，正文用"skills"
 * MCP：协议名称保留英文，不翻译为"应用"
 * 翻译的术语：命令(Commands)、插件(Plugins)、会话(Sessions)、应用(Apps)
 *
 * 复数处理：中文无语法复数，按 i18n/index.ts 的约定只定义基键
 * （en 的 *_one / *_other 由 resolvePluralKey 回退到基键）。
 */

export default {
'''
lines = [f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)}," for k, v in result.items()]
open("zh.ts", "w", encoding="utf-8").write(header + "\n".join(lines) + "\n} as const;\n")

print("\n".join(report))
