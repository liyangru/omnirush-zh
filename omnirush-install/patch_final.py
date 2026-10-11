# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第六层 —— 收尾：模型选择、命令面板、扩展卡、状态提示等

覆盖 scan_region.py 全量扫描后剩下的可见文案。这些字符串都很独特，
按 remaining2.json 的精确偏移替换，替换前校验内容一致。
"""
import json, os, re, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()
CAND = os.path.join(HERE, "remaining2.json")

T = {
    # ---- 模型选择器：模型说明 ----
    "Strong agentic coding · 19 GB · 256K context": "强智能体编程 · 19 GB · 256K 上下文",
    "Good for smaller Macs · about 4.7 GB": "适合较小的 Mac · 约 4.7 GB",
    "${HW(n,s.model)} (not available)": "${HW(n,s.model)}（不可用）",
    "Connect OpenAI, Anthropic, Google, or OpenRouter without changing model identities.":
        "连接 OpenAI、Anthropic、Google 或 OpenRouter，且不改变模型标识。",

    # ---- 扩展 / 技能卡说明 ----
    "Instructions that teach agents specialized workflows": "教智能体掌握特定工作流的说明",
    "Tools and services connected through MCP": "通过 MCP 连接的工具与服务",
    "Connected organization apps and services": "已连接的组织应用与服务",
    "Extensions that add tools and behavior": "增加工具与行为的扩展",
    "Specialized agents available in conversations": "对话中可用的专用智能体",
    "Slash commands available in the composer": "输入框中可用的斜杠命令",

    # ---- 命令面板 ----
    "Choose any session, including one from another workspace": "选择任意会话，包括来自其他工作区的会话",
    "Start an empty session beside this one": "在此会话旁开启一个空会话",
    "Choose the LLM that runs your next prompts": "选择运行后续提示词的大模型",
    "Deep search every session, including message content": "深度搜索所有会话，包括消息内容",
    "Search within the current conversation": "在当前对话中搜索",
    "Toggle the integrated terminal panel for this workspace": "切换此工作区的内置终端面板",
    "Switch to the next session in this workspace": "切换到此工作区的下一个会话",
    "Switch to the previous session in this workspace": "切换到此工作区的上一个会话",
    "Advance the focused conversation to its next available thinking or reasoning effort.":
        "把当前对话推进到下一个可用的思考或推理强度。",
    "Switch the focused conversation to its next favorite model.": "把当前对话切换到下一个收藏的模型。",
    "Open the in-app command palette so the next choice is visible.": "打开应用内命令面板，让下一个选项可见。",
    "Open the provider connection modal, optionally pre-filtered to a specific provider.":
        "打开提供商连接弹窗，可选地预先筛选到某个提供商。",
    "Provider id to pre-select, e.g. 'anthropic', 'openai', 'google'.":
        "要预选的提供商 id，例如 'anthropic'、'openai'、'google'。",
    "Create a workspace at the given folder path without showing the file picker dialog, optionally labeling its project for analytics.":
        "在指定文件夹路径创建工作区，不弹出文件选择对话框，可选地为其项目打标签用于分析。",
    "Optional project name used to group the workspace's sessions in analytics.":
        "可选的项目名称，用于在分析中归组该工作区的会话。",
    "Refetch the session list of one workspace so sessions created outside this window appear in the sidebar.":
        "重新获取某个工作区的会话列表，让在此窗口之外创建的会话出现在侧栏中。",
    "Workspace id whose session list should be refetched.": "需要重新获取会话列表的工作区 id。",
    "Exchange a desktop handoff grant string to sign in without the browser flow.":
        "用桌面交接授权串登录，无需走浏览器流程。",
    "The raw handoff grant string.": "原始交接授权串。",
    "Optional Den base URL.": "可选的 Den 基础网址。",
    "Return the current cloud sign-in status and user.": "返回当前的云端登录状态和用户。",

    # ---- 状态提示 ----
    "Connected to ${c}.": "已连接到 ${c}。",
    "Worker is reachable, but tasks failed to load: ${r}": "Worker 可访问，但任务加载失败：${r}",
    "Model ${s}/${r} is not available.": "模型 ${s}/${r} 不可用。",
    "${Ge.name} does not have a stored organization credential yet.":
        "${Ge.name} 尚未保存组织凭据。",
    "${Ne.name} does not have a stored organization credential yet.":
        "${Ne.name} 尚未保存组织凭据。",
    "${q} The download page is open in your browser.": "${q} 下载页面已在浏览器中打开。",
    "${e.tab.name} (double-click to rename)": "${e.tab.name}（双击重命名）",
    "${e.name} logo": "${e.name} 标志",
    "${Dt} has been updated": "${Dt} 已更新",
    "${Dt} is no longer available": "${Dt} 已不可用",
    "${ln.name??ln.id} was added to ${an}": "${ln.name??ln.id} 已添加到 ${an}",
    "Installed ${Ne.item.name} with ${Ne.item.files.length} component${Ne.item.files.length===1?\"\":\"s\"}.":
        "已安装 ${Ne.item.name}，包含 ${Ne.item.files.length} 个组件。",
    "Removed ${Tt.item.name}.": "已移除 ${Tt.item.name}。",
    "Removed ${Ne.name}.": "已移除 ${Ne.name}。",

    # ---- 设置 → 高级：引擎配置说明 ----
    "Workspace-level omnirush.ai config owned by the user/project.":
        "由用户/项目拥有的工作区级 omnirush.ai 配置。",
    "User-level engine configuration.": "用户级引擎配置。",
    "App-managed runtime values stored outside workspace files.":
        "由应用管理、存储在工作区文件之外的运行时值。",
    "The object the app injects into omnirush.ai at runtime.":
        "应用在运行时注入到 omnirush.ai 的对象。",
}

# 扩展卡片的 prompt 前缀由第七层 patch_ext.py 处理（它们是双引号字符串，不是模板字面量）

src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)

edits = []
hit = 0
miss = set(T)
cands = json.load(open(CAND, encoding="utf-8"))
for it in cands:
    txt = it["text"]
    if txt not in T:
        continue
    off = it["offset"]
    if src[off] not in "\"'`":
        continue
    if src[off + 1: off + 1 + len(txt)] != txt:
        continue
    edits.append((off + 1, off + 1 + len(txt), T[txt]))
    hit += 1
    miss.discard(txt)

print(f"字典命中: {hit} 处")
if miss:
    print(f"未命中（{len(miss)} 条）:")
    for m in sorted(miss):
        print(f"   · {m[:95]}")

edits.sort(key=lambda e: e[0], reverse=True)
prev = None
for s, e, _ in edits:
    if prev is not None and e > prev:
        sys.exit(f"!! 区间重叠 @{s}")
    prev = s

out = src
for s, e, new in edits:
    out = out[:s] + new + out[e:]
print(f"\n共替换 {len(edits)} 处，长度 {orig_len} -> {len(out)} ({len(out)-orig_len:+d})")

tmp = BUNDLE + ".tmpcheck.mjs"
open(tmp, "w", encoding="utf-8", newline="").write(out)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    os.remove(tmp)
    sys.exit(f"!! node --check 失败:\n{r.stdout}\n{r.stderr}")
print("node --check ✓")
os.replace(tmp, BUNDLE)
print(f"已写入 {BUNDLE}")
