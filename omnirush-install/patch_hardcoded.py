# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第二层 —— 硬编码 UI 文案

背景：官方只把一部分界面文字接入了 i18n，另有一批文案直接写在 JSX / 数组字面量里，
无论选什么语言都显示英文（截图里的 "Audit trail"、"Workflows"、
"what would you like to work on?"、6 张启动卡片、"sign in to omnirush.ai" 等）。

本脚本对已安装的渲染层 bundle 做两类替换：
  A. 锚点替换：带代码上下文的精确片段（唯一性由上下文保证）
  B. 偏移替换：来自 hardcoded_ui.json 的字符串字面量（偏移已校验）

执行顺序上先把 A、B 两类改动都换算成 (start, end, new) 区间，
再按区间倒序统一写回，避免改一处导致后面偏移错位。

前置条件：先运行 patch_zh.py（注入补全版 zh 语言包 + 清空白名单 + 默认中文）。
本脚本不做还原，直接在当前 bundle 上追加。
"""
import json, os, re, sys, subprocess, shutil
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()
CANDIDATES = os.path.join(HERE, "hardcoded_ui.json")

# ---------------------------------------------------------------- B. 偏移替换表
# 键 = bundle 中的原文；值 = 中文。未列出的候选一律不动（组件名、品牌名、
# 调试日志、纯模板串等）。
TRANS = {
    # ---- 语言选择器 ----
    "English": "英语",
    "Japanese": "日语",
    "Chinese (Simplified)": "简体中文",
    "Vietnamese": "越南语",
    "Portuguese (BR)": "葡萄牙语（巴西）",
    "Thai": "泰语",
    "French": "法语",
    "Catalan": "加泰罗尼亚语",
    "Spanish": "西班牙语",
    "Russian": "俄语",
    # ---- 计算机选择 ----
    "Failed to load tasks": "加载任务失败",
    "Start a task on your cloud computer": "在你的云电脑上开始任务",
    "Start a task on your connected desktop computer": "在你已连接的桌面电脑上开始任务",
    "[skill ${e.name}]": "[技能 ${e.name}]",
    # ---- 遥测维度校验 ----
    "Dimension type must start with a lowercase letter and contain only lowercase letters, numbers, dots, underscores, or hyphens.":
        "维度类型必须以小写字母开头，且只能包含小写字母、数字、点、下划线或连字符。",
    "Dimension value must contain only letters, numbers, dots, underscores, colons, slashes, or hyphens.":
        "维度值只能包含字母、数字、点、下划线、冒号、斜杠或连字符。",
    "Dimension metadata is too large.": "维度元数据过大。",
    "dimensionType and dimensionValue must be supplied together.": "dimensionType 与 dimensionValue 必须同时提供。",
    "Open console": "打开控制台",
    # ---- 系统通知 ----
    "Task completed": "任务已完成",
    "The session finished running.": "会话已结束运行。",
    "Task failed": "任务失败",
    "Permission needed": "需要授权",
    "Question needs your answer": "有提问等待你回答",
    "Some features and appearance settings are managed by your administrator.": "部分功能和外观设置由你的管理员管理。",
    # ---- 架构不匹配提示页 ----
    "Architecture mismatch": "架构不匹配",
    "Install the correct omnirush.ai build": "安装正确的 omnirush.ai 版本",
    "Running app": "正在运行的应用",
    "Your system": "你的系统",
    "Download correct version": "下载正确版本",
    "Open release page": "打开发布页面",
    "Why omnirush.ai stopped here": "omnirush.ai 为何在此停止",
    # ---- 企业版登录 ----
    "Unable to finish omnirush.ai Enterprise sign-in.": "无法完成 omnirush.ai 企业版登录。",
    "Unable to save this omnirush.ai server.": "无法保存此 omnirush.ai 服务器。",
    "omnirush.ai Enterprise": "omnirush.ai 企业版",
    "Link this app to your organization": "将此应用关联到你的组织",
    "Enter your workspace address — the page where you downloaded this app. Sign-in finishes in your browser and returns here.":
        "输入你的工作区地址——即你下载此应用的那个页面。登录会在浏览器中完成并返回此处。",
    "Workspace address": "工作区地址",
    "Allow and start": "允许并开始",
    "Check again": "再次检查",
    "Paste the code from your browser": "粘贴浏览器中显示的代码",
    # ---- 组织选择 / 工作区准备 ----
    "Your organization": "你的组织",
    "Loading organizations...": "正在加载组织…",
    "Choose your organization": "选择你的组织",
    "Unable to load organizations.": "无法加载组织。",
    "The application update could not be prepared.": "无法准备应用更新。",
    "Workspace branding could not be prepared.": "无法准备工作区品牌信息。",
    "Preparing workspace identity": "正在准备工作区身份",
    "Preparing workspace...": "正在准备工作区…",
    "Workspace identity is ready": "工作区身份已就绪",
    "Why restart?": "为什么要重启？",
    "Restarting refreshes the workspace name and icon across your operating system and installs the prepared application update.":
        "重启会在你的操作系统中刷新工作区名称与图标，并安装已准备好的应用更新。",
    "Continue without restarting": "不重启继续",
    "Loading available resources...": "正在加载可用资源…",
    "You have access to the following resources.": "你可以访问以下资源。",
    "AI Providers": "AI 提供商",
    "Models you can use in your workspace.": "你的工作区中可使用的模型。",
    "App stores with extensions and plugins for your workspace.": "为你的工作区提供扩展和插件的应用商店。",
    "No resources have been configured for this organization yet.": "此组织尚未配置任何资源。",
    "Add AI providers or marketplaces from the omnirush.ai Cloud dashboard.": "请从 omnirush.ai Cloud 控制台添加 AI 提供商或应用市场。",
    "Providers are added to your workspace automatically. Collections are available from Cloud settings.":
        "提供商会自动加入你的工作区。集合可在 Cloud 设置中获取。",
    "Unable to select organization.": "无法选择组织。",
    "Select the organization whose cloud resources should be connected to this workspace.":
        "选择要将其云资源连接到此工作区的组织。",
    "Search organizations...": "搜索组织…",
    "No organizations match your search.": "没有匹配的组织。",
    # ---- 命令面板 ----
    "Open sessions": "打开会话",
    "Navigate to the main session view.": "跳转到主会话视图。",
    "Open general settings": "打开通用设置",
    "Navigate to general settings.": "跳转到通用设置。",
    "Open extensions": "打开扩展",
    "Browse the skills and MCPs available to this agent.": "浏览此智能体可用的技能与 MCP。",
    "Open provider settings": "打开提供商设置",
    "Navigate to AI provider settings.": "跳转到 AI 提供商设置。",
    "Open authorized folder settings": "打开授权文件夹设置",
    "Navigate to authorized folders and file access settings.": "跳转到授权文件夹与文件访问设置。",
    "Open appearance settings": "打开外观设置",
    "Navigate to appearance settings.": "跳转到外观设置。",
    "Open a settings panel": "打开某个设置面板",
    "Navigate to a specific settings panel by tab id.": "按标签页 id 跳转到指定设置面板。",
    "Go back": "后退",
    "Navigate back one entry in history.": "在历史记录中后退一步。",
    "Go forward": "前进",
    "Navigate forward one entry in history.": "在历史记录中前进一步。",
    "What can omnirush.ai do?": "omnirush.ai 能做什么？",
    "List the main capabilities of omnirush.ai.": "列出 omnirush.ai 的主要能力。",
    "Browse the web": "浏览网页",
    "Control a browser to navigate, read page content, and automate web tasks.":
        "控制浏览器进行导航、读取页面内容并自动化网页任务。",
    "AI model providers": "AI 模型提供商",
    "Connect Anthropic, OpenAI, Google, OpenRouter, Ollama, or other LLM providers.":
        "连接 Anthropic、OpenAI、Google、OpenRouter、Ollama 或其他大模型提供商。",
    "File management": "文件管理",
    "Read, write, and organize files in your workspace.": "在你的工作区中读取、写入和整理文件。",
    "Write and run code": "编写并运行代码",
    "Generate, edit, and execute code with full tool access.": "在完整工具权限下生成、编辑并执行代码。",
    "Install specialized skill packs for specific workflows.": "为特定工作流安装专用技能包。",
    "Automations": "自动化",
    "Schedule recurring tasks and background agents.": "安排周期性任务和后台智能体。",
    "Share sessions": "共享会话",
    "Share workspace sessions with collaborators via omnirush.ai Cloud.":
        "通过 omnirush.ai Cloud 与协作者共享工作区会话。",
    "Update pending quota wrap": "更新待处理的配额收尾",
    "Show or settle a local, user-approved context wrap offer.": "显示或结算本地、经用户批准的上下文收尾提议。",
    "Choose Wrap up again to retry, or keep working.": "选择“收尾”可重试，或继续工作。",
    "Save a handoff for this session?": "为此次会话保存交接？",
    "Saving a handoff for this session.": "正在为此次会话保存交接。",
    "Wrap up": "收尾",
    # ---- 云工作区状态 ----
    "omnirush.ai Web needs an active plan": "omnirush.ai Web 需要有效的订阅",
    "Your organization does not have an active omnirush.ai Web subscription or complimentary access. Get omnirush.ai Web in Den to start your cloud workspace.":
        "你的组织没有有效的 omnirush.ai Web 订阅或赠送权限。请在 Den 中获取 omnirush.ai Web 以启动云工作区。",
    "Workspace needs attention": "工作区需要处理",
    "We couldn’t start the sandbox. Retry, or sign out and reconnect.": "无法启动沙箱。请重试，或退出登录后重新连接。",
    "Couldn’t check your workspace": "无法检查你的工作区",
    "omnirush.ai Cloud didn’t answer. Your sandbox may still be running, so try checking again.":
        "omnirush.ai Cloud 没有响应。你的沙箱可能仍在运行，请稍后再试。",
    "Still working on it…": "仍在处理中…",
    "This is taking longer than usual. You can keep waiting or check again.": "这比平时耗时更长。你可以继续等待，或再次检查。",
    "Starting your workspace…": "正在启动你的工作区…",
    "Usually under a minute. We’ll open it the moment it’s ready.": "通常不到一分钟。就绪后我们会立即打开。",
    "Updating your workspace…": "正在更新你的工作区…",
    "We’re applying the latest omnirush.ai image. Your files and sessions come along.":
        "正在应用最新的 omnirush.ai 镜像。你的文件和会话会一并保留。",
    "Waking your workspace…": "正在唤醒你的工作区…",
    "Your sandbox is coming back online. We’ll open it as soon as it’s ready.":
        "你的沙箱正在重新上线。就绪后我们会立即打开。",
    "omnirush.ai Web plan required": "需要 omnirush.ai Web 订阅",
    "Provisioning your workspace…": "正在配置你的工作区…",
    "We’ll open your workspace automatically when it’s ready.": "工作区就绪后会自动打开。",
    "Select and copy for support": "选择并复制以便提交支持",
    "Update now": "立即更新",
    "Takes about 30 seconds. Your files and sessions come along.": "大约需要 30 秒。你的文件和会话会一并保留。",
    "omnirush.ai couldn't start": "omnirush.ai 无法启动",
    "Return to a version that works on this computer.": "回退到在此电脑上可用的版本。",
    "Restore previous version": "恢复上一版本",
    "Pick another version": "选择其他版本",
    # ---- 终端 ----
    "New tab": "新建标签页",
    "Terminal ${a.nextNumber}": "终端 ${a.nextNumber}",
    "Starting…": "正在启动…",
    "Could not start the terminal.": "无法启动终端。",
    # ---- 连接器 / 预览 ----
    "Failed to load organization MCP connections.": "加载组织 MCP 连接失败。",
    "Failed to start the connection.": "启动连接失败。",
    "Failed to disconnect the account.": "断开账户失败。",
    "Could not open setup.": "无法打开设置。",
    "Find a connector…": "查找连接器…",
    "No connectors match your search.": "没有匹配的连接器。",
    "Open preview": "打开预览",
    "Try this app in the preview, ask for changes here, then choose Save to use it again.":
        "在预览中试用此应用，在这里提出修改，然后选择“保存”以便再次使用。",
    "Copy these details when reporting the rendering problem.": "报告渲染问题时请复制这些详细信息。",
    "${t} interactive view": "${t} 交互视图",
    "App preview": "应用预览",
    "Open ${s} in default app": "在默认应用中打开 ${s}",
    "${u.panel} settings": "${u.panel} 设置",
    # ---- 会话步骤 ----
    "Choose an option or approve the request to continue.": "选择一个选项或批准请求以继续。",
    "This step stopped before it finished. Retry to continue.": "此步骤在完成前已停止。重试以继续。",
    "No terminal result was observed. This step may still be running; check the session before retrying.":
        "未观察到终端结果。此步骤可能仍在运行，重试前请检查会话。",
    "Thinking…": "正在思考…",
    "Tool step unavailable": "工具步骤不可用",
    "Waiting for your action": "等待你的操作",
    "Task interrupted": "任务已中断",
    "Open ${s} in Artifacts": "在制品面板中打开 ${s}",
    "Skill: ${e.name}": "技能：${e.name}",
}

# ---------------------------------------------------------------- A. 锚点替换表
# (原文片段, 中文片段, 预期出现次数)
ANCHORS = [
    # 侧栏 · 审计日志
    ('children:"Audit trail"', 'children:"审计日志"', 2),
    ('"aria-label":"Audit trail",title:"A local activity record reconstructed from this task and workspace. Integrity verification is not enabled in this version."',
     '"aria-label":"审计日志",title:"根据此任务与工作区重建的本地活动记录。此版本未启用完整性校验。"', 1),
    ('"aria-label":"Audit trail has a failure"', '"aria-label":"审计日志存在失败记录"', 1),
    ('"aria-label":"Audit trail is waiting for approval"', '"aria-label":"审计日志正在等待批准"', 1),
    # 侧栏 · 工作流
    ('"aria-label":"Workflows",title:"Build sequential workflows and choose connected models for each step"',
     '"aria-label":"工作流",title:"构建顺序化工作流，并为每一步选择已连接的模型"', 1),
    ('children:"Workflows"', 'children:"工作流"', 1),
    ('"Workflows & model routing"', '"工作流与模型路由"', 1),
    # 工作流面板导航标签
    ('{value:"routing",label:"Model routing"}', '{value:"routing",label:"模型路由"}', 1),
    ('{value:"workflows",label:"Workflows"}', '{value:"workflows",label:"工作流"}', 1),
    ('{value:"runs",label:"Run history"}', '{value:"runs",label:"运行历史"}', 1),
    # 侧栏 · 设置按钮（两处分支）
    ('tooltip:"Settings","aria-label":"Settings",children:[o.jsx($w,{className:"size-4"}),o.jsx("span",{children:"Settings"})]',
     'tooltip:"设置","aria-label":"设置",children:[o.jsx($w,{className:"size-4"}),o.jsx("span",{children:"设置"})]', 2),
    # 侧栏 · 账户行
    ('||"Your account":"sign in to omnirush.ai"', '||"你的账号":"登录 omnirush.ai"', 1),
    ('t?.reauthorizationRequired?"Sign in again to continue":"Use omnirush.ai models with your account"',
     't?.reauthorizationRequired?"请重新登录以继续":"使用你的账号访问 omnirush.ai 模型"', 1),
    ('`connected to ${a}`:"omnirush.ai models ready"', '`已连接到 ${a}`:"omnirush.ai 模型已就绪"', 1),
    (':s:"Sign in to omnirush.ai"', ':s:"登录 omnirush.ai"', 1),
    # 首页问候语（按时段切换）
    ('e<5?{title:"what would you like to work on?",subtitle:"describe the outcome you need"}:e<12?{title:"good morning. how can I help?",subtitle:"what are we getting done?"}:e<17?{title:"good afternoon. how can I help?",subtitle:"what should we tackle?"}:e<22?{title:"good evening. how can I help?",subtitle:"what are we getting done?"}:{title:"what would you like to work on?",subtitle:"describe the outcome you need"}',
     'e<5?{title:"你想做什么？",subtitle:"描述你期望的结果"}:e<12?{title:"早上好，我能帮上什么忙？",subtitle:"我们今天要完成什么？"}:e<17?{title:"下午好，我能帮上什么忙？",subtitle:"我们要处理什么？"}:e<22?{title:"晚上好，我能帮上什么忙？",subtitle:"我们今天要完成什么？"}:{title:"你想做什么？",subtitle:"描述你期望的结果"}', 1),
    # 首页 6 张启动卡片的标题 + 描述（prompt 单独处理，见下）
    ('title:"Fix a hard bug",description:"Reproduce it, find the root cause, fix and test"',
     'title:"修复疑难 Bug",description:"复现问题、定位根因、修复并验证"', 1),
    ('title:"Make it faster",description:"Measure, find the bottleneck, show before/after"',
     'title:"提升性能",description:"测量、定位瓶颈、给出前后对比"', 1),
    ('title:"Fix the build",description:"Get the build, CI or Docker setup passing"',
     'title:"修复构建",description:"让构建、CI 或 Docker 配置通过"', 1),
    ('title:"Refactor or migrate",description:"Move a module or library, keep behaviour the same"',
     'title:"重构或迁移",description:"迁移模块或依赖库，保持行为不变"', 1),
    ('title:"Build a real feature",description:"Design, implement across the code, add tests"',
     'title:"实现完整功能",description:"设计、跨代码库实现、补充测试"', 1),
    ('title:"Systems work",description:"Networking, storage, scheduling or concurrency"',
     'title:"系统层工作",description:"网络、存储、调度或并发"', 1),
    # 首页 6 张启动卡片的 prompt（标题/描述走偏移表）
    ('prompt:"There\'s a bug in this project: {describe the symptom}. Reproduce it with a failing test or command first, find the root cause, fix it, and run the tests until they pass."',
     'prompt:"这个项目有个 Bug：{describe the symptom}。先用一个失败的测试或命令复现它，找到根因并修复，然后运行测试直到全部通过。"', 1),
    ('prompt:"{Part} of this project is too slow. Measure it first (benchmark or profiler), find the bottleneck, optimise it, and show before/after numbers."',
     'prompt:"这个项目的 {Part} 太慢了。先做测量（基准测试或性能分析器），找到瓶颈并优化，然后给出优化前后的数据对比。"', 1),
    ('prompt:"The build/CI/Docker setup for this project is broken or missing: {what}. Get it building from a clean checkout and make the build pass."',
     'prompt:"这个项目的构建/CI/Docker 配置已损坏或缺失：{what}。请从干净检出开始让它可以构建，并让构建通过。"', 1),
    ('prompt:"Migrate {module/library} in this project to {target}. Update every caller, keep behaviour the same, and run the tests after each step."',
     'prompt:"把这个项目中的 {module/library} 迁移到 {target}。更新所有调用方，保持行为不变，并在每一步之后运行测试。"', 1),
    ('prompt:"Add {feature} to this project end to end: design it, implement it across the code that needs it, add tests, and run them."',
     'prompt:"为这个项目端到端地添加 {feature}：先设计，再在需要的代码中实现，补充测试并运行。"', 1),
    ('prompt:"Work on {the networking/storage/scheduler/concurrency part} of this project: {goal}. Write tests that exercise it and run them."',
     'prompt:"处理这个项目的{the networking/storage/scheduler/concurrency part}：{goal}。编写覆盖它的测试并运行。"', 1),
    # 组织预设提示词
    ('OTt=["Organization prompt 1","Organization prompt 2","Organization prompt 3"]',
     'OTt=["组织提示词 1","组织提示词 2","组织提示词 3"]', 1),
    ('||"Organization prompt"', '||"组织提示词"', 1),
    # 命令面板 · 分组标题与设置页字面量
    ('{recent:"Recent",actions:"Actions",settings:"Settings",sessions:"Sessions"}',
     '{recent:"最近",actions:"操作",settings:"设置",sessions:"会话"}', 1),
    ('case"general":return"Settings";', 'case"general":return"设置";', 1),
    ('breadcrumb:"Settings",group:"settings"', 'breadcrumb:"设置",group:"settings"', 1),
    ('breadcrumb:"Settings › Library"', 'breadcrumb:"设置 › 资料库"', 1),
    ('breadcrumb:"Settings › Advanced"', 'breadcrumb:"设置 › 高级"', 1),
    ('title:a==="advanced"?"Advanced settings":uf(a)', 'title:a==="advanced"?"高级设置":uf(a)', 1),
    # 账户状态面板
    ('"Connected":"Sign in to your account"', '"已连接":"登录你的账号"', 1),
    ('"omnirush.ai models are ready on this Mac."', '"omnirush.ai 模型已在此 Mac 上就绪。"', 1),
    ('"Your system keyring is not available right now. Sign in again to continue."',
     '"系统密钥环当前不可用。请重新登录以继续。"', 1),
    ('"Your session expired. Sign in again to continue."', '"你的会话已过期。请重新登录以继续。"', 1),
    ('"Sign in in your browser, then return here."', '"请在浏览器中登录，然后返回此处。"', 1),
    ('"The omnirush.ai account service has not been configured for this build."',
     '"此构建未配置 omnirush.ai 账户服务。"', 1),
]

# ---------------------------------------------------------------- 执行
src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)
edits = []          # (start, end, new, tag)
problems = []

# ---- A. 锚点 ----
a_hits = 0
for old, new, expect in ANCHORS:
    ms = list(re.finditer(re.escape(old), src))
    if len(ms) != expect:
        problems.append(f"[A] 锚点出现 {len(ms)} 次（预期 {expect}）: {old[:70]!r}")
        continue
    for m in ms:
        edits.append((m.start(), m.end(), new, f"A:{old[:40]}"))
        a_hits += 1
print(f"A. 锚点替换: {a_hits} 处")

# ---- B. 偏移 ----
cands = json.load(open(CANDIDATES, encoding="utf-8"))
b_hits = 0
for it in cands:
    t = it["text"]
    if t not in TRANS:
        continue
    off = it["offset"]
    if src[off] not in "\"'`":
        problems.append(f"[B] @{off} 不是引号: {src[off]!r}")
        continue
    if src[off + 1: off + 1 + len(t)] != t:
        problems.append(f"[B] @{off} 内容不符: 期望 {t[:40]!r}")
        continue
    edits.append((off + 1, off + 1 + len(t), TRANS[t], f"B:{t[:40]}"))
    b_hits += 1
print(f"B. 偏移替换: {b_hits} 处")

if problems:
    print("\n!! 以下条目未能匹配，已跳过：")
    for p in problems:
        print("   " + p)
    if any(p.startswith("[A]") for p in problems):
        sys.exit("\n锚点缺失会导致漏译，请修正后重跑。")

# ---- 区间倒序写回，先做重叠检查 ----
edits.sort(key=lambda e: e[0], reverse=True)
prev_start = None
for s, e, new, tag in edits:
    if prev_start is not None and e > prev_start:
        sys.exit(f"!! 区间重叠: {tag} [{s},{e}) 与前一区间起点 {prev_start} 冲突")
    prev_start = s

out = src
for s, e, new, tag in edits:
    out = out[:s] + new + out[e:]
print(f"总替换 {len(edits)} 处，长度 {orig_len} -> {len(out)} ({len(out)-orig_len:+d})")

# ---- 语法自检后再落盘 ----
tmp = BUNDLE + ".tmpcheck.mjs"   # 必须用 .mjs：.js 会让 node --check 静默返回 0
open(tmp, "w", encoding="utf-8", newline="").write(out)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    os.remove(tmp)
    sys.exit(f"!! node --check 失败:\n{r.stdout}\n{r.stderr}")
print("node --check ✓")
os.replace(tmp, BUNDLE)
print(f"已写入 {BUNDLE}")
