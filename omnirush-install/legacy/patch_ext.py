# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第七层 —— 扩展定义区 + 计算机操作面板 + 提供商开关

第六层遗留：三个 composer prompt 前缀用的是双引号字符串（不是模板字面量），
锚点写成了反引号形式，导致 0 命中。本层一并修正，并补齐：
  · 扩展卡片定义（omnirush-browser / computer-use / ollama）的 name / setup / cta
  · 计算机操作状态面板的全部状态文案
  · 提供商启用开关的按钮文案

所有替换均采用「唯一锚点 + 出现次数校验」，避免误伤 i18n 数据区
（例如 "Enabled" 在 i18n 区 @433478 也有，绝不能用全局 replace）。
"""
import os, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()

# (锚点, 译文, 预期出现次数)
ANCHORS = [
    # ---- 扩展卡片的 composer prompt 前缀（双引号字符串，各 2 处）----
    ('"Use the omnirush.ai Browser extension to "', '"使用 omnirush.ai 浏览器扩展来 "', 2),
    ('"Use Computer Use to "', '"使用计算机操作来 "', 2),
    ('"Use the Ollama extension to "', '"使用 Ollama 扩展来 "', 2),

    # ---- omnirush.ai Browser 扩展 ----
    ('"omnirush.ai Browser is ready by default in desktop workspaces."',
     '"omnirush.ai 浏览器在桌面工作区中默认即可用。"', 1),
    ('ref:"omnirush-browser",label:"Enabled"',
     'ref:"omnirush-browser",label:"已启用"', 1),

    # ---- Computer Use 扩展 ----
    ('name:"Computer Use"', 'name:"计算机操作"', 1),
    ('"Computer Use supports macOS 14+, Windows, and Linux X11. On macOS, grant Accessibility and Screen Recording. Windows and Linux control require the app in front; your input pauses control. Wayland requires a separate desktop portal integration. For each session, choose an app window and allow reading, app controls, or mouse and keyboard. Choose Allow and start in omnirush.ai. Your input interrupts control; Stop in the preview ends access."',
     '"计算机操作支持 macOS 14+、Windows 和 Linux X11。在 macOS 上，请授予辅助功能与屏幕录制权限。'
     'Windows 和 Linux 的控制要求应用处于前台，你的输入会暂停控制。Wayland 需要单独的桌面门户集成。'
     '每个会话中，选择一个应用窗口，并允许读取、应用控制或鼠标键盘操作。在 omnirush.ai 中选择「允许并开始」。'
     '你的输入会中断控制；在预览中点击「停止」即结束访问。"', 1),
    ('primaryCta:"Enable Computer Use"', 'primaryCta:"启用计算机操作"', 1),
    ('secondaryCta:"Check desktop access"', 'secondaryCta:"检查桌面访问权限"', 1),

    # ---- Ollama 扩展 ----
    ('"Run Ollama locally, choose or pull a model, then add it as an OmniRush provider."',
     '"在本地运行 Ollama，选择或拉取模型，然后将其添加为 OmniRush 提供商。"', 1),
    ('"Add Ollama model"', '"添加 Ollama 模型"', 1),
    ('"Pull model"', '"拉取模型"', 1),

    # ---- Computer Use 状态面板 ----
    ('"Computer Use could not create a CLI connection. Check desktop access and try again."',
     '"计算机操作无法创建 CLI 连接。请检查桌面访问权限后重试。"', 1),
    ('"Refresh Computer Use status"', '"刷新计算机操作状态"', 1),
    ('"Ready \u00b7 app access is approved when a session starts"',
     '"就绪 \u00b7 会话开始时会批准应用访问"', 1),
    ('"Connected \u00b7 finish macOS permissions below"',
     '"已连接 \u00b7 请在下方完成 macOS 权限设置"', 1),
    ('"Connected \u00b7 check desktop access below"',
     '"已连接 \u00b7 请在下方检查桌面访问权限"', 1),
    ('"Permissions are ready. Enable Computer Use for this workspace."',
     '"权限已就绪。为此工作区启用计算机操作。"', 1),
    ('"Set up Computer Use for this workspace"', '"为此工作区设置计算机操作"', 1),
    ('"Desktop access is unavailable on this session"', '"此会话无法使用桌面访问权限"', 1),
    ('"Enabling\u2026"', '"正在启用\u2026"', 1),
    ('"Allow macOS access":"Check desktop access"',
     '"允许 macOS 访问权限":"检查桌面访问权限"', 1),

    # ---- 提供商启用开关 ----
    ('"Enable this provider"', '"启用此提供商"', 1),
    ('"Disable this provider"', '"停用此提供商"', 1),
    ('children:e.isDisabled?"Enable":"Enabled"', 'children:e.isDisabled?"启用":"已启用"', 1),
]

src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)

edits = []
fail = 0
for old, new, expect in ANCHORS:
    n = src.count(old)
    if n != expect:
        print(f"  !! 出现 {n} 次（预期 {expect}）: {old[:80]!r}")
        fail += 1
        continue
    if expect == 1:
        i = src.find(old)
        edits.append((i, i + len(old), new))
    else:
        i = -1
        while True:
            i = src.find(old, i + 1)
            if i < 0:
                break
            edits.append((i, i + len(old), new))
    print(f"  \u2713 {old[:72]!r}")

edits.sort(key=lambda e: e[0], reverse=True)
prev = None
for s, e, _ in edits:
    if prev is not None and e > prev:
        sys.exit(f"!! 区间重叠 @{s}")
    prev = s

out = src
for s, e, new in edits:
    out = out[:s] + new + out[e:]
print(f"\n替换 {len(edits)} 处，失败 {fail} 条，长度 {orig_len} -> {len(out)} ({len(out)-orig_len:+d})")
if fail:
    sys.exit("!! 存在未命中锚点，已中止")

tmp = BUNDLE + ".tmpcheck.mjs"
open(tmp, "w", encoding="utf-8", newline="").write(out)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    os.remove(tmp)
    sys.exit(f"!! node --check 失败:\n{r.stdout}\n{r.stderr}")
print("node --check \u2713")
os.replace(tmp, BUNDLE)
print(f"已写入 {BUNDLE}")
