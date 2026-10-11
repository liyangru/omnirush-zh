# -*- coding: utf-8 -*-
"""验证设置总览页汉化结果。

新版把设置总览重构成了两个 switch 函数（标签映射 + 描述映射），
硬编码的几条英文分别在这两个函数里，且不带句末句号。
"""
import os
import re

from _bundle import detect_bundle

s = open(detect_bundle(), encoding="utf-8").read()

# 新版：标签映射 / 描述映射里硬编码的英文（不带句号）
GONE = [
    'return"Preferences";', 'return"Permissions";', 'return"Voice";',
    'return"Settings";', 'return"设置 general"',
    'return"Connect services that provide AI models"',
    'return"Default model, reasoning, and compaction"',
    'return"Authorized folders and file access"',
    'return"Runtime, engine, recovery, and developer options"',
    'return"Theme, font size, and display"',
    'return"Dictation, microphone, and hotkey"',
    'return"Environment variables and paths"',
    'return"App version and update channel"',
    # 旧版残留的带句号形式（旧 build 的锚点）
    '"Default model, reasoning, and compaction."',
    '"Authorized folders and file access."',
    '"Runtime, engine, recovery, and developer options."',
    '"Connect services that provide AI models."',
    '"Theme, font size, and display."',
    '"Dictation, microphone, and hotkey."',
    '"Environment variables and paths."',
    '"App version and update channel."',
    'children:"Account"}', 'children:"Workspace"}', 'children:"Global"}',
    '"Overview of all settings"',
    '"Voice is transcribed by our cloud speech provider.',
    '"Sub-agents are the helpers',
    '"How hard sub-agents think.',
    '"Same as main agent"',
    '"Privacy"',
]
PRESENT = [
    'return"偏好设置";', 'return"权限";', 'return"语音";', 'return"设置";',
    'return"连接提供 AI 模型的服务"',
    'return"默认模型、推理与上下文压缩"',
    'return"授权文件夹与文件访问"',
    'return"听写、麦克风与快捷键"',
    'children:"账号"}', 'children:"工作区"}', 'children:"全局"}',
    '"所有设置的概览"', '"登录"',
    '语音由我们的云端语音提供商转写。',
    '子智能体是主智能体通过 task 工具',
    '子智能体的思考强度。',
    '"与主智能体相同"',
]

def count_outside(text, needle):
    """统计 needle 在 i18n 数据区之外的出现次数"""
    lo = text.find('"account.mcp_connected_one"')
    hi = text.find(";function Ws(", lo) if lo >= 0 else -1
    n, i = 0, -1
    while True:
        i = text.find(needle, i + 1)
        if i < 0:
            break
        if not (lo >= 0 and lo <= i < hi):
            n += 1
    return n


print("=== 设置总览：英文是否消失 ===")
bad = 0
for m in GONE:
    c = count_outside(s, m)
    print(f"  {'✓' if c == 0 else '✗'} {c:>3}  {m}")
    bad += 1 if c else 0

print("\n=== 设置总览：中文是否就位 ===")
miss = 0
for m in PRESENT:
    c = s.count(m)
    print(f"  {'✓' if c > 0 else '✗'} {c:>3}  {m}")
    miss += 0 if c else 1

print(f"\n残留英文: {bad} | 缺失中文: {miss}")

# 设置总览两个 switch 函数区域再审一遍
print("\n=== 标签映射 / 描述映射区域剩余英文 ===")
STR = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
CJK = re.compile(r"[\u4e00-\u9fff]")
found = 0
for kw in ('function pIe(e)', 'case"general":return'):
    i = s.find(kw)
    if i < 0:
        print(f"  （未找到 {kw}）")
        continue
    seg = s[i:i + 1400]
    seen = set()
    for m in STR.finditer(seg):
        t = m.group(1)
        if not t or t in seen or CJK.search(t):
            continue
        if len(re.findall(r"[A-Za-z]{2,}", t)) < 2:
            continue
        if re.match(r"^[a-z0-9._/-]+$", t):
            continue
        seen.add(t)
        print(f"  {t[:100]}")
        found += 1
if not found:
    print("  ✓ 无")
