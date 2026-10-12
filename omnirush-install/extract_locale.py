# -*- coding: utf-8 -*-
"""从当前 bundle 重新抽取官方语言包，写成 ../omnirush-i18n/en.ts（和 zh.original.ts）。

为什么需要它
------------
应用升级后官方语言包会变（3.4.3 就新增了 16 个键、移除/改写了若干）。
merge.py / verify_final.py 都依赖 en.ts，所以升级后要重新抽一次。

要点
----
bundle 里的字符串值有三种定界符：`"…"`、`'…'`、`` `…` ``（含换行的值必为反引号
模板）。只匹配双引号会漏掉一批键——这正是之前 en.ts 少了 8 个键的原因。
本脚本对三种定界符都做完整解析（反引号支持 `${}` 嵌套计数）。

用法：
    python extract_locale.py                # 抽取 en，并对比旧文件
    python extract_locale.py --zh           # 同时抽取官方 zh（覆盖 zh.original.ts）
    python extract_locale.py --diff-only    # 只报告差异，不写文件
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
I18N = os.path.join(os.path.dirname(HERE), "omnirush-i18n")
sys.path.insert(0, HERE)
from _bundle import detect_bundle  # noqa: E402

EN_ANCHOR = '"account.mcp_connected_one":"'
ZH_ANCHOR = '"app.compact_command_desc":"'


def scan_balanced(s, start, oc, cc):
    """字符串感知的括号匹配（跳过三种引号内的括号）。"""
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
            elif c == oc:
                depth += 1
            elif c == cc:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


ESC = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f", "v": "\v",
       "0": "\0", "\\": "\\", '"': '"', "'": "'", "`": "`", "/": "/",
       "$": "$", "\n": ""}


def unescape(raw):
    """还原 JS 字符串转义。"""
    out = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        if i + 1 >= n:
            out.append("\\")
            break
        e = raw[i + 1]
        if e == "u" and i + 5 < n:
            try:
                out.append(chr(int(raw[i + 2:i + 6], 16)))
                i += 6
                continue
            except ValueError:
                pass
        if e == "x" and i + 3 < n:
            try:
                out.append(chr(int(raw[i + 2:i + 4], 16)))
                i += 4
                continue
            except ValueError:
                pass
        out.append(ESC.get(e, e))
        i += 2
    return "".join(out)


def parse_object(obj):
    """解析 JS 对象字面量，返回 [(key, value)]，支持三种定界符。"""
    pairs = []
    i = 0
    n = len(obj)
    while i < n:
        while i < n and obj[i] in " \t\r\n,":
            i += 1
        if i >= n or obj[i] != '"':
            i += 1
            continue
        # key
        j = i + 1
        while j < n:
            if obj[j] == "\\":
                j += 2
                continue
            if obj[j] == '"':
                break
            j += 1
        key = unescape(obj[i + 1:j])
        i = j + 1
        while i < n and obj[i] in " \t\r\n":
            i += 1
        if i >= n or obj[i] != ":":
            continue
        i += 1
        while i < n and obj[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        d = obj[i]
        if d in "\"'":
            j = i + 1
            while j < n:
                if obj[j] == "\\":
                    j += 2
                    continue
                if obj[j] == d:
                    break
                j += 1
            pairs.append((key, unescape(obj[i + 1:j])))
            i = j + 1
        elif d == "`":
            j = i + 1
            depth = 0
            while j < n:
                c = obj[j]
                if c == "\\":
                    j += 2
                    continue
                if c == "$" and j + 1 < n and obj[j + 1] == "{":
                    depth += 1
                    j += 2
                    continue
                if c == "}" and depth > 0:
                    depth -= 1
                    j += 1
                    continue
                if c == "`" and depth == 0:
                    break
                j += 1
            pairs.append((key, unescape(obj[i + 1:j])))
            i = j + 1
        else:
            i += 1
    return pairs


def extract(anchor):
    s = open(detect_bundle(), encoding="utf-8").read()
    i = s.find(anchor)
    if i < 0:
        raise SystemExit(f"!! 找不到锚点 {anchor!r}")
    start = s.rfind("{", 0, i)
    end = scan_balanced(s, start, "{", "}")
    return parse_object(s[start:end + 1])


def read_keys(path):
    if not os.path.exists(path):
        return set()
    return set(re.findall(r'^\s*"([^"]+)"\s*:', open(path, encoding="utf-8").read(), re.M))


HEADER_EN = (
    "/**\n"
    " * English translations\n"
    " * Professional terms (Skills, Plugins, Commands, Sessions, OpenCode, "
    "OpenPackage, omnirush.ai) are NOT translated\n"
    " */\n\n"
    "export default {\n"
)


def write_ts(path, pairs, header):
    body = "\n".join(
        f"  {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},"
        for k, v in pairs)
    open(path, "w", encoding="utf-8", newline="\n").write(header + body + "\n} as const;\n")


def report(label, pairs, path):
    keys = [k for k, _ in pairs]
    print(f"\n=== {label} ===")
    print(f"  抽取到 {len(keys)} 键（去重后 {len(set(keys))}）")
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        print(f"  ⚠️ 重复键 {len(dup)}: {dup[:5]}")
    interp = [k for k, v in pairs if "${" in v]
    if interp:
        print(f"  含 ${{}} 插值的值: {len(interp)} -> {interp[:5]}")
    old = read_keys(path)
    if old:
        new_k = set(keys) - old
        gone_k = old - set(keys)
        print(f"  与现有文件对比：新增 {len(new_k)}，消失 {len(gone_k)}")
        for k in sorted(new_k)[:40]:
            print(f"    + {k}")
        for k in sorted(gone_k)[:40]:
            print(f"    - {k}")
    return keys


def main():
    diff_only = "--diff-only" in sys.argv
    do_zh = "--zh" in sys.argv

    en = extract(EN_ANCHOR)
    en_path = os.path.join(I18N, "en.ts")
    report("官方 en", en, en_path)
    if not diff_only:
        write_ts(en_path, en, HEADER_EN)
        print(f"  ✓ 已写入 {en_path}")

    if do_zh:
        zh = extract(ZH_ANCHOR)
        zh_path = os.path.join(I18N, "zh.original.ts")
        report("官方 zh", zh, zh_path)
        if not diff_only:
            write_ts(zh_path, zh, HEADER_EN.replace("English translations", "官方原版中文"))
            print(f"  ✓ 已写入 {zh_path}")


if __name__ == "__main__":
    main()
