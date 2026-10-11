# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第五层 —— 设置总览页

截图里的英文全部来自「写死在代码里的设置项数组与标签映射」：
  * eHt（工作区分组的三张卡片）
  * tHt（全局分组的五张卡片）
  * uf()  —— tab id → 标签（preferences / permissions / voice 三个是硬编码）
  * 描述映射 —— voice / general 两个是硬编码
  * 分组标题 children:"Account" / "Workspace" / "Global"
  * 账号卡片的 "Sign in" 按钮、`Account server: ${host}` 模板

术语与 zh.ts 保持一致：工作区 / 全局 / 高级 / 外观 / 环境变量 / 更新。
"""
import os, subprocess, sys
from _bundle import detect_bundle

ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()

A = [
    # ---- 分组标题 ----
    ('tracking-[0.15em] text-dls-secondary",children:"Account"}',
     'tracking-[0.15em] text-dls-secondary",children:"账号"}', 1),
    ('tracking-[0.15em] text-dls-secondary",children:"Workspace"})',
     'tracking-[0.15em] text-dls-secondary",children:"工作区"})', 1),
    ('tracking-[0.15em] text-dls-secondary",children:"Global"})',
     'tracking-[0.15em] text-dls-secondary",children:"全局"})', 1),
    # 工作区筛选 chip
    ('onClick:()=>t.setFilter("workspace"),children:"Workspace"}',
     'onClick:()=>t.setFilter("workspace"),children:"工作区"}', 1),

    # ---- 工作区分组卡片数组 eHt ----
    ('const eHt=[{tab:"preferences",icon:B$,title:"Preferences",desc:"Default model, reasoning, and compaction."},'
     '{tab:"permissions",icon:Ihe,title:"Permissions",desc:"Authorized folders and file access."},'
     '{tab:"advanced",icon:H$,title:"Advanced",desc:"Runtime, engine, recovery, and developer options."}]',
     'const eHt=[{tab:"preferences",icon:B$,title:"偏好设置",desc:"默认模型、推理与上下文压缩。"},'
     '{tab:"permissions",icon:Ihe,title:"权限",desc:"已授权的文件夹与文件访问。"},'
     '{tab:"advanced",icon:H$,title:"高级",desc:"运行时、引擎、恢复与开发者选项。"}]', 1),

    # ---- 全局分组卡片数组 tHt ----
    ('tHt=[{tab:"ai",icon:Jx,title:"AI 提供商",desc:"Connect services that provide AI models."},'
     '{tab:"appearance",icon:Phe,title:"Appearance",desc:"Theme, font size, and display."},'
     '{tab:"voice",icon:F$,title:"Voice",desc:"Dictation, microphone, and hotkey."},'
     '{tab:"environment",icon:jb,title:"Environment",desc:"Environment variables and paths."},'
     '{tab:"updates",icon:rd,title:"Updates",desc:"App version and update channel."}]',
     'tHt=[{tab:"ai",icon:Jx,title:"AI 提供商",desc:"连接提供 AI 模型的服务。"},'
     '{tab:"appearance",icon:Phe,title:"外观",desc:"主题、字体大小与显示。"},'
     '{tab:"voice",icon:F$,title:"语音",desc:"听写、麦克风与快捷键。"},'
     '{tab:"environment",icon:jb,title:"环境变量",desc:"环境变量与路径。"},'
     '{tab:"updates",icon:rd,title:"更新",desc:"应用版本与更新通道。"}]', 1),

    # ---- uf()：tab 标签映射 ----
    ('case"preferences":return"Preferences";case"permissions":return"Permissions";',
     'case"preferences":return"偏好设置";case"permissions":return"权限";', 1),
    ('case"appearance":return b("settings.tab_appearance");case"voice":return"Voice";',
     'case"appearance":return b("settings.tab_appearance");case"voice":return"语音";', 1),

    # ---- 描述映射 ----
    ('case"voice":return"Dictation, microphone, and hotkey";',
     'case"voice":return"听写、麦克风与快捷键";', 1),
    ('case"general":return"Overview of all settings";',
     'case"general":return"所有设置的概览";', 1),

    # ---- 账号卡片 ----
    ('children:s?"Waiting…":"Sign in"', 'children:s?"等待中…":"登录"', 1),
    ('`Connected to ${t}`:`Account server: ${t}`',
     '`已连接到 ${t}`:`账号服务器：${t}`', 1),
    ('`${Math.round(g.percent)}% used`', '`${Math.round(g.percent)}% 已用`', 1),

    # ---- 侧栏账户行 ----
    ('A?"omnirush.ai Cloud":"Sign in"', 'A?"omnirush.ai Cloud":"登录"', 1),
    ('A?"Restoring your session":"Sync with omnirush.ai Cloud"',
     'A?"正在恢复你的会话":"与 omnirush.ai Cloud 同步"', 1),

    # ---- 连接器认证方式标签 ----
    ('const _8t={oauth:"Sign in",oauth_client:"Admin setup",api_key:"API key",instant:"Ready to add",suite:"Guided setup"}',
     'const _8t={oauth:"登录",oauth_client:"管理员配置",api_key:"API 密钥",instant:"可立即添加",suite:"引导式设置"}', 1),

    # ---- 登出提示 ----
    ('"the account server"', '"账号服务器"', 1),
    ('`Signed out on this device and revoked its device session on ${n}.`',
     '`已在此设备退出登录，并已撤销其在 ${n} 上的设备会话。`', 2),
    ('`Signed out on this device. ${n} had already revoked this device session.`',
     '`已在此设备退出登录。${n} 早已撤销该设备会话。`', 1),
    ('`Signed out on this device. ${n} has no remote sign-out endpoint, so the device session was not revoked there.`',
     '`已在此设备退出登录。${n} 没有远程登出端点，因此未在该处撤销设备会话。`', 1),
    ('`Signed out on this device. ${n} could not be reached, so the device session was not revoked there.`',
     '`已在此设备退出登录。无法连接到 ${n}，因此未在该处撤销设备会话。`', 1),
    ('`Signed out on this device. The device session on ${n} could not be revoked.`',
     '`已在此设备退出登录。无法撤销 ${n} 上的设备会话。`', 1),
]

src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)

edits, problems = [], []
for old, new, expect in A:
    n = src.count(old)
    if n != expect:
        problems.append(f"出现 {n} 次（预期 {expect}）: {old[:80]!r}")
        continue
    start = 0
    while True:
        i = src.find(old, start)
        if i < 0:
            break
        edits.append((i, i + len(old), new))
        start = i + len(old)
    print(f"  ✓ {old[:66]!r}")

if problems:
    print("\n!! 以下锚点未匹配：")
    for p in problems:
        print("   " + p)
    sys.exit("锚点缺失，中止。")

edits.sort(key=lambda e: e[0], reverse=True)
prev = None
for s, e, _ in edits:
    if prev is not None and e > prev:
        sys.exit(f"!! 区间重叠 @{s}")
    prev = s

out = src
for s, e, new in edits:
    out = out[:s] + new + out[e:]
print(f"\n替换 {len(edits)} 处，长度 {orig_len} -> {len(out)} ({len(out)-orig_len:+d})")

tmp = BUNDLE + ".tmpcheck.mjs"
open(tmp, "w", encoding="utf-8", newline="").write(out)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    os.remove(tmp)
    sys.exit(f"!! node --check 失败:\n{r.stdout}\n{r.stderr}")
print("node --check ✓")
os.replace(tmp, BUNDLE)
print(f"已写入 {BUNDLE}")
