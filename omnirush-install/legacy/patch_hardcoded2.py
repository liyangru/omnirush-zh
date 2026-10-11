# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第三层 —— 应用自身其余硬编码 UI 文案

在 patch_zh.py（i18n 数据层）与 patch_hardcoded.py（首页/侧栏）之后运行。
本层覆盖：提供商连接流程、会话输入区、内置浏览器、应用与仪表盘、自动化、
设置面板标题、语音输入、模型/Ollama、扩展与计算机操作、常见错误提示等。

替换方式：按 remaining_en.json 记录的精确偏移逐条替换字符串内容，
每条都校验「该偏移处的内容 == 原文」，不匹配则跳过并报告。
"""
import json, os, re, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()
CAND = os.path.join(HERE, "remaining_en.json")

# 允许被替换的属性名（含 "?" = 无法判定前导属性名，但这些原文是我们手工挑选的）
OK_PROPS = {
    "children", "title", "subtitle", "label", "description", "placeholder",
    "aria-label", "ariaLabel", "prompt", "tooltip", "heading", "caption",
    "hint", "emptyTitle", "emptyDescription", "confirmLabel", "cancelLabel",
    "alt", "message", "text", "note", "summary", "help", "badge", "name",
    "subtitleText", "body", "cta", "actionLabel", "detail", "sub", "meta",
    "error", "desc", "value", "reason", "userNotice", "searchText",
    "recommendedAction", "?", "null",
}

T = [
    # ============ 组织策略（设置 → 权限） ============
    ("Allow users to add and use models that are not deployed through OmniRush.ai Cloud.",
     "允许用户添加并使用未经 OmniRush.ai Cloud 部署的模型。"),
    ("Allow users to use the built in models provided by OpenCode.",
     "允许用户使用 OpenCode 提供的内置模型。"),
    ("Allow users to create or configure more than one workspace on their machine.",
     "允许用户在本机创建或配置多个工作区。"),
    ("Allow users to access and change the desktop app settings.",
     "允许用户访问并修改桌面应用设置。"),
    ("Allow users to install and manage extensions locally.",
     "允许用户在本地安装和管理扩展。"),
    ("Allow users to see and use OmniRush.ai's built-in extensions, including browser, image, and local-provider extensions.",
     "允许用户查看并使用 OmniRush.ai 的内置扩展，包括浏览器、图像和本地提供商扩展。"),
    ("Allow users to opt into experimental Alpha desktop updates.",
     "允许用户选择加入实验性 Alpha 桌面更新。"),
    ("Show the Getting Started page to new users.", "向新用户显示“快速上手”页面。"),
    ("Action-based Automations are created by Web and run in OmniRush.ai Cloud.",
     "基于动作的自动化由 Web 创建，并在 OmniRush.ai Cloud 中运行。"),

    # ============ 扩展：内置浏览器 / 计算机操作 ============
    ("Automate the built-in browser panel that stays visible inside omnirush.ai.",
     "自动化 omnirush.ai 内常驻可见的内置浏览器面板。"),
    ("Work in the app and window you approve. Read, use accessible controls, or allow mouse and keyboard control with a small window preview.",
     "在你批准的应用和窗口中工作。可读取内容、使用无障碍控件，或在带小窗预览的情况下允许鼠标键盘控制。"),
    ("Computer Use MCP", "计算机操作 MCP"),
    ("Computer Use session runtime", "计算机操作会话运行时"),
    ("Setup instructions", "设置说明"),
    ("Accessibility and Screen Recording", "辅助功能与屏幕录制"),
    ("Verify Computer Use MCP", "验证计算机操作 MCP"),
    ("MCP server connected", "MCP 服务器已连接"),
    ("Accessibility permission", "辅助功能权限"),
    ("Screen Recording permission", "屏幕录制权限"),
    ("Local model provider at http://localhost:11434.", "本地模型提供商，地址 http://localhost:11434。"),
    ("Ollama API", "Ollama API"),
    ("Check local models", "检查本地模型"),
    ("Ollama provider", "Ollama 提供商"),

    # ============ 杂项 ============
    ("Unknown error", "未知错误"),
    ("Organization policies active", "组织策略已生效"),
    ("Sign out", "退出登录"),
    ("Show more", "显示更多"),
    ("Skills, connections, and tools your agent can use.", "你的智能体可用的技能、连接和工具。"),
    ("Your handoff is saved. You can keep working while tokens remain.",
     "你的交接已保存。只要还有 token，你就可以继续工作。"),
    ("Keep working", "继续工作"),
    ("Update available", "有可用更新"),
    ("Technical details", "技术详情"),

    # ============ 提供商连接流程 ============
    ("Auto-updates are available in packaged builds only.", "自动更新仅在打包版本中可用。"),
    ("Show the downloaded file", "显示已下载的文件"),
    ("Failed to complete OAuth", "OAuth 授权未完成"),
    ("Failed to start OAuth", "OAuth 授权启动失败"),
    ("API key saved locally on this device.", "API 密钥已保存在本设备上。"),
    ("Failed to save API key", "保存 API 密钥失败"),
    ("Connect providers", "连接提供商"),
    ("Sign in to services or use providers managed by your organization.",
     "登录各项服务，或使用你所在组织管理的提供商。"),
    ("Loading providers…", "正在加载提供商…"),
    ("Filter providers by name or ID", "按名称或 ID 筛选提供商"),
    ("Arrow keys to navigate, Enter to select.", "方向键导航，回车选择。"),
    ("Choose how you'd like to connect.", "选择你要使用的连接方式。"),
    ("Paste your API key to connect.", "粘贴你的 API 密钥以连接。"),
    ("API key", "API 密钥"),
    ("Finish OAuth by pasting the authorization code.", "粘贴授权码以完成 OAuth。"),
    ("Complete sign-in in your browser, then paste the code here.",
     "在浏览器中完成登录，然后在此粘贴代码。"),
    ("Authorization code", "授权码"),
    ("Paste code", "粘贴代码"),
    ("Open browser again", "再次打开浏览器"),
    ("Waiting for browser confirmation.", "等待浏览器确认。"),
    ("You'll need to sign in to your OpenAI account and provide the code below.",
     "你需要登录 OpenAI 账号并提供下方代码。"),
    ("The first time you do this you'll need to enable Device auth in your account settings.",
     "首次操作需要在你的账号设置中启用设备授权。"),
    ('When you\'re ready, copy the code below, and click "Open Browser".',
     "准备好后，复制下方代码并点击“打开浏览器”。"),
    ("Sign in in the browser tab we just opened. We will complete the connection automatically.",
     "在我们刚打开的浏览器标签页中登录。连接会自动完成。"),
    ("Confirmation code", "确认码"),
    ("Authorization checks will start after you click Open Browser.",
     "点击“打开浏览器”后将开始授权检查。"),
    ("Checking connection status automatically…", "正在自动检查连接状态…"),
    ("This window will close once the provider is connected.", "提供商连接成功后此窗口会自动关闭。"),

    # ============ 图表渲染错误 ============
    ("Diagram source is too large to render safely.", "图表源码过大，无法安全渲染。"),
    ("Diagram source contains unsafe directives or resources.", "图表源码包含不安全的指令或资源。"),
    ("Diagram is too complex to render safely.", "图表过于复杂，无法安全渲染。"),
    ("The engine did not provide an individual result for this action. See the execution details.",
     "引擎未为此操作提供单独结果。请查看执行详情。"),
    ("Method not found", "未找到该方法"),
    ("Change model", "更换模型"),

    # ============ 会话输入区 / 运行状态 ============
    ("Shared folder upload failed", "共享文件夹上传失败"),
    ("Message acceptance is unknown", "消息接收状态未知"),
    ("It may already be running. Sending is paused to avoid duplicates. Check acceptance or stop the run; Stop does not resend the message.",
     "它可能已在运行。为避免重复，发送已暂停。请检查接收状态或停止运行；“停止”不会重发消息。"),
    ("Check acceptance", "检查接收状态"),
    ("Opening session…", "正在打开会话…"),
    ("No AI model connected.", "未连接任何 AI 模型。"),
    ("Add a provider to run tasks.", "添加一个提供商即可运行任务。"),
    ("Open Connect", "打开连接"),
    ("Your unsent message is saved. Clear the current draft to restore it.",
     "你未发送的消息已保存。清空当前草稿即可恢复。"),
    ("Restore unsent message", "恢复未发送的消息"),
    ("Remote access", "远程访问"),
    ("Off by default. Turn this on only when you want this worker reachable from another machine.",
     "默认关闭。仅当你希望此 worker 可从其他机器访问时才开启。"),
    ("Connection details", "连接详情"),
    ("Enable remote access and click Save to restart the worker and reveal the live connection details for this workspace.",
     "启用远程访问并点击“保存”以重启 worker，并显示此工作区的实时连接详情。"),
    ("Optional collaborator access", "可选的协作者访问"),
    ("Routine access without permission approvals.", "常规访问，无需逐次批准权限。"),
    ("Could not create the conversation. Try again.", "无法创建会话。请重试。"),
    ("Clear the current draft to restore the unsent message", "清空当前草稿以恢复未发送的消息"),
    ("connect a model provider", "连接一个模型提供商"),
    ("add an api key for openai, anthropic, google, or openrouter so tasks can run.",
     "为 openai、anthropic、google 或 openrouter 添加 API 密钥，以便运行任务。"),
    ("Close tab", "关闭标签页"),

    # ============ 应用与仪表盘 ============
    ("This removes the saved app from everyone’s dashboards and the app list. Its workflow and past results stay available.",
     "这会从所有人的仪表盘和应用列表中移除此已保存的应用。其工作流和过往结果仍然保留。"),
    ("Connect a workspace to open the preview.", "连接一个工作区以打开预览。"),
    ("Could not open a conversation. Try again.", "无法打开会话。请重试。"),
    ("Sign in to open this app.", "登录后即可打开此应用。"),
    ("Your draft is kept. Ask for changes in the conversation, then save the app to use it again.",
     "你的草稿已保留。在对话中提出修改，然后保存应用以便再次使用。"),
    ("Keep the workflow and app together for future use. Each new run supplies its own results.",
     "将工作流与应用一起保存以备将来使用。每次运行都会产生各自的结果。"),
    ("App name", "应用名称"),
    ("My dashboard · Sharing stays the same", "我的仪表盘 · 共享设置保持不变"),
    ("Already-open results keep their current app version.", "已打开的结果保持当前应用版本。"),
    ("The app could not be saved. Try again.", "无法保存应用。请重试。"),
    ("This app could not be opened.", "无法打开此应用。"),
    ("Try again", "重试"),
    ("Preview unavailable. Open externally to view this file.", "预览不可用。请在外部打开以查看此文件。"),
    ("Could not save changes.", "无法保存更改。"),
    ("Could not open this file.", "无法打开此文件。"),
    ("Could not show this file in your file manager.", "无法在你的文件管理器中显示此文件。"),
    ("Close artifact", "关闭制品"),
    ("Show in folder", "在文件夹中显示"),
    ("Open externally", "在外部打开"),
    ("Failed to load artifact", "加载制品失败"),

    # ============ 内置浏览器面板 ============
    ("Open a new page in the built-in browser.", "在内置浏览器中打开新页面。"),
    ("Files & artifacts", "文件与制品"),
    ("View files and artifacts created in this session.", "查看本次会话中创建的文件与制品。"),
    ("Browse the skills and connections available to your agent.", "浏览你的智能体可用的技能与连接。"),
    ("No files or artifacts yet", "暂无文件或制品"),
    ("Files and artifacts created in this session will appear here automatically.",
     "本次会话中创建的文件与制品会自动显示在这里。"),
    ("Choose a destination", "选择目标位置"),
    ("Open a tool or return here whenever you want to switch.", "打开一个工具，或随时返回此处进行切换。"),
    ("Sync logins from another browser", "从其他浏览器同步登录信息"),
    ("While enabled, omnirush.ai keeps reading only the browser profile and sites you select. It never changes the source browser.",
     "启用后，omnirush.ai 只会持续读取你选择的浏览器配置和站点。它绝不会修改来源浏览器。"),
    ("No supported browser profile with saved logins was found on this computer.",
     "此电脑上未找到包含已保存登录信息的受支持浏览器配置。"),
    ("Enabling sync permits continuing reads from this profile for only the checked sites.",
     "启用同步后，仅对勾选的站点允许继续读取此配置。"),
    ("Pause, change a site's access, or disconnect from Settings → Permissions → Browser logins.",
     "可在“设置 → 权限 → 浏览器登录”中暂停、修改站点访问权限或断开连接。"),
    ("Not now", "暂不"),
    ("Keep selected logins in sync", "保持所选登录信息同步"),
    ("Choose one browser profile and the sites omnirush.ai may keep reading. Nothing starts until you enable sync.",
     "选择一个浏览器配置，以及 omnirush.ai 可继续读取的站点。在你启用同步之前不会开始任何操作。"),
    ("Set up sync", "设置同步"),
    ("Built-in browser", "内置浏览器"),
    ("Enter URL...", "输入网址…"),
    ("Site tools", "站点工具"),
    ("Actions offered by this page. Review the website and the requested action before allowing it.",
     "此页面提供的操作。允许之前请先检查网站和请求的操作。"),
    ("Recent activity", "最近活动"),
    ("Arguments and results are not retained in this activity view.",
     "此活动视图不保留参数和结果。"),
    ("Browser panel is only available in the desktop app.", "浏览器面板仅在桌面应用中可用。"),
    ("Close panel", "关闭面板"),
    ("Tab suspended", "标签页已挂起"),
    ("Reload opens the saved URL, not the previous page state.",
     "重新加载会打开已保存的网址，而非之前的页面状态。"),
    ("Panel destinations", "面板目标"),
    ("New tab", "新建标签页"),
    ("New terminal with…", "新建终端…"),
    ("Hide terminal", "隐藏终端"),
    ("Retry connection", "重试连接"),
    ("Close pane", "关闭窗格"),
    ("This workspace does not have a connected runtime.", "此工作区没有已连接的运行时。"),
    ("Back to parent chat", "返回上级对话"),
    ("Find in conversation (⌘F)", "在对话中查找（⌘F）"),
    ("Clears acknowledged providers + org onboarding so they trigger again",
     "清除已确认的提供商和组织引导记录，使其再次触发"),
    ("Reset notifications", "重置通知"),
    ("Workspace or session not found", "未找到工作区或会话"),
    ("All models", "全部模型"),
]

# 由列表转字典
TRANS = dict(T)

# 追加第二段（放在另一个文件里以保持可读性）
try:
    from trans2_part2 import T2
    TRANS.update(dict(T2))
except ImportError:
    pass

# ------------------------------------------------------------------ 执行
src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)
cands = json.load(open(CAND, encoding="utf-8"))

edits = []
hit = {}
miss = set(TRANS)
for it in cands:
    txt = it["text"]
    if txt not in TRANS or it["prop"] not in OK_PROPS:
        continue
    off = it["offset"]
    q = src[off]
    if q not in "\"'`":
        continue
    if src[off + 1: off + 1 + len(txt)] != txt:
        continue
    new = TRANS[txt]
    if q in new or "${" in new:
        print(f"  !! 跳过（译文含定界符 {q!r} 或 ${{）：{txt[:50]!r}")
        continue
    edits.append((off + 1, off + 1 + len(txt), new))
    hit[txt] = hit.get(txt, 0) + 1
    miss.discard(txt)

print(f"待替换字面量: {len(edits)} 处，覆盖 {len(hit)} 个不同文案")
if miss:
    print(f"\n未在候选清单中命中的条目（{len(miss)} 条）：")
    for m in sorted(miss):
        print(f"   · {m[:100]}")

edits.sort(key=lambda e: e[0], reverse=True)
prev = None
for s, e, _ in edits:
    if prev is not None and e > prev:
        sys.exit(f"!! 区间重叠 @{s}")
    prev = s

out = src
for s, e, new in edits:
    out = out[:s] + new + out[e:]
print(f"\n长度 {orig_len} -> {len(out)} ({len(out)-orig_len:+d})")

tmp = BUNDLE + ".tmpcheck.mjs"
open(tmp, "w", encoding="utf-8", newline="").write(out)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    os.remove(tmp)
    sys.exit(f"!! node --check 失败:\n{r.stdout}\n{r.stderr}")
print("node --check ✓")
os.replace(tmp, BUNDLE)
print(f"已写入 {BUNDLE}")
