# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第八层 —— 全量 UI 前端文案清扫

前七层解决的是「整块界面」，本层做地毯式清扫：JSX 文本片段、按钮/标签、
状态文案、长说明段落、面向用户的错误提示。

关键设计：
  · 定界符自动识别 —— 同一个内容可能是 "..."、'...' 或 `...`（含 ${} 插值的
    在压缩后一定是反引号）。脚本依次尝试三种定界符，取「i18n 数据区之外」
    命中数等于预期的那一种。
  · i18n 数据区 [lang_lo, lang_hi] 全程排除，绝不触碰官方语言包。
  · 所有替换以 (start, end, new) 区间表示，按 start 降序写回，避免偏移漂移。
"""
import os, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = detect_bundle()

src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)
LANG_LO = src.find('"account.mcp_connected_one"')
LANG_HI = src.find(";function Ws(", LANG_LO)


def occurrences(a):
    """返回字面量在 i18n 数据区之外的所有出现位置"""
    res = []
    i = -1
    while True:
        i = src.find(a, i + 1)
        if i < 0:
            break
        if not (LANG_LO <= i < LANG_HI):
            res.append(i)
    return res


# ---------------------------------------------------------------------------
# T: (内容, 译文, i18n 区外预期出现次数)  —— 定界符自动识别
# ---------------------------------------------------------------------------
T = [
    # ===== 架构不匹配 / 启动引导 =====
    ("Your application is running the ", "你的应用运行的是 ", 1),
    ("After installing the correct ", "安装正确的 ", 1),
    ("omnirush.ai blocks startup when the installed app architecture does not match the machine architecture. This prevents runtime sidecars, browser tooling, and update downloads from continuing on the wrong build.",
     "当已安装的应用架构与机器架构不匹配时，omnirush.ai 会阻止启动。这样可以避免运行时附属进程、浏览器工具和更新下载在错误的构建上继续运行。", 1),

    # ===== 登录 / 组织引导 =====
    ("Connect this app to ", "将此应用连接到 ", 1),
    ("Welcome to ", "欢迎使用 ", 1),
    ("Sign in to ", "登录到 ", 1),
    ("Manage access in Den", "在 Den 中管理访问权限", 1),
    ("Claim workspace and continue", "认领工作区并继续", 1),
    ("Applying ", "正在应用 ", 1),
    ("Restart omnirush.ai once to finish applying ", "重启 omnirush.ai 一次以完成应用 ", 1),
    ("Restart omnirush.ai", "重启 omnirush.ai", 1),
    ("Open omnirush.ai Cloud", "打开 omnirush.ai Cloud", 1),
    ("Your ", "你的 ", 1),
    ("Showing ", "显示 ", 1),
    ("Get omnirush.ai Web", "获取 omnirush.ai 网页版", 1),

    # ===== 通用标签 / 片段 =====
    ("Env vars:", "环境变量：", 1),
    ("Browse all ", "浏览全部 ", 1),
    ("Technical details (", "技术详情（", 1),
    ("Last activity: ", "最近活动：", 1),
    ("Delete \u201c", "删除\u201c", 2),
    ("\u201d? The workflow cannot be restored; run history will remain.",
     "\u201d？工作流无法恢复；运行历史将保留。", 1),
    ("Use this view for future results", "以后用此视图查看结果", 1),
    ("New results from ", "新结果来自 ", 1),
    ("Sync is active for ", "同步已对以下对象启用：", 1),
    ("Enable sync for ", "为以下对象启用同步：", 1),
    ("Terminal \u00b7 ", "终端 \u00b7 ", 1),
    ("Version ", "版本 ", 1),
    ("Revision ", "修订 ", 1),
    ("Shared ", "共享 ", 1),
    ("Updated ", "已更新 ", 1),
    ("Update ", "更新 ", 1),
    ("Display name", "显示名称", 1),
    ("Project name ", "项目名称 ", 1),
    ("Sync error: ", "同步错误：", 1),
    ("Stored keys: ", "已存储的密钥：", 1),
    ("User-owned keys: ", "用户自有密钥：", 1),
    ("Reveal in Finder", "在访达中显示", 2),
    ("Spinning\u2026", "旋转中\u2026", 1),
    ("Reproducible \u2713", "可复现 \u2713", 1),
    ("See why", "查看原因", 1),
    ("Daytona folder path", "Daytona 文件夹路径", 1),
    ("Set up", "设置", 2),

    # ===== 模板字面量（含 ${} 插值，压缩后必为反引号）=====
    ("Files (${E})", "文件（${E}）", 2),
    ("Connected to ${c}.", "已连接到 ${c}。", 1),
    ("No workspace matched ${lt}", "没有匹配 ${lt} 的工作区", 1),
    ("Session is unavailable: ${xt}", "会话不可用：${xt}", 1),
    ("Browser provider is not available yet: ${Mn}", "浏览器提供商尚不可用：${Mn}", 1),
    ('the "${ji}" skill', '\u201c${ji}\u201d技能', 1),
    ("Stop tracking ${$.name||$.value}", "停止跟踪 ${$.name||$.value}", 1),
    ("Unknown action: ${U}", "未知操作：${U}", 1),
    ("Unknown query: ${U.id}", "未知查询：${U.id}", 1),
    ("Unknown command: ${U.id}", "未知命令：${U.id}", 1),
    ("Action is disabled: ${q.label}", "操作已禁用：${q.label}", 1),
    ("Query is disabled: ${V.label}", "查询已禁用：${V.label}", 1),
    ("Already acting: ${x.current}${$}", "正在执行：${x.current}${$}", 1),
    ("Already acting: ${x.current}${L}", "正在执行：${x.current}${L}", 1),
    ("omnirush.ai context changed from revision ${U.expectedRevision} to ${Z}.",
     "omnirush.ai 上下文已从修订 ${U.expectedRevision} 变为 ${Z}。", 1),

    # ===== 按钮 / 标签 / 状态 =====
    ("Create and activate", "创建并激活", 1),
    ("Save key", "保存密钥", 1),
    ("Ollama (local)", "Ollama（本地）", 1),
    ("Best local agent", "最佳本地智能体", 1),
    ("Fast local model", "快速本地模型", 1),
    ("Read a window", "读取窗口", 1),
    ("Use app controls", "使用应用控制", 1),
    ("Use mouse and keyboard", "使用鼠标和键盘", 1),
    ("Provider/model", "提供商/模型", 1),
    ("Cloud provider", "云端提供商", 1),
    ("Cloud providers", "云端提供商", 1),

    # ===== 长说明段落 =====
    ("Each conversation uses its own tabs in the built-in browser. Background work stays with its conversation. Review website access and actions in the browser panel, or choose Take over to sign in and Resume browser when finished.",
     "每个对话在内置浏览器中使用自己的标签页。后台工作保留在所属对话中。在浏览器面板中查看网站访问与操作记录，或选择「接管」以登录，完成后选择「恢复浏览器」。", 1),
    ("Sign in directly in the built-in browser; your session stays available across browser tasks. Your regular browser profile and login syncing are separate. Site tools support the imperative WebMCP document API; declarative forms and external browser control are not supported yet.",
     "直接在内置浏览器中登录；你的会话在各项浏览器任务间保持可用。你的常规浏览器配置和登录同步是相互独立的。站点工具支持命令式 WebMCP 文档 API；声明式表单和外部浏览器控制尚不支持。", 1),
    ("The tool call failed. The engine did not provide an individual error; see the execution details.",
     "工具调用失败。引擎未提供具体错误，请查看执行详情。", 1),
    ('MCP component "${we}" could not be installed: no server config with a "url" or "command" was found.',
     'MCP 组件\u201c${we}\u201d无法安装：未找到包含 "url" 或 "command" 的服务器配置。', 1),
    ('MCP component "${we}" could not be installed because it is not active.',
     'MCP 组件\u201c${we}\u201d无法安装，因为它未处于活动状态。', 1),

    # ===== 面向用户的提示 / 校验错误 =====
    ("Something went wrong", "出了点问题", 1),
    ("Enter a GitHub repository URL.", "请输入 GitHub 仓库网址。", 1),
    ("The focused model has fewer than two thinking modes.", "当前聚焦的模型少于两种思考模式。", 1),
    ("Add a favorite model before cycling favorites.", "请先添加收藏模型，再切换收藏。", 1),
    ("The built-in browser is not available here.", "此处无法使用内置浏览器。", 1),
    ("Built-in browser is not available.", "内置浏览器不可用。", 3),
    ("Missing URL.", "缺少网址。", 1),
    ("Missing tabId.", "缺少 tabId。", 2),
    ("Session transcript is not mounted", "会话记录尚未挂载", 1),
    ("No messages are visible in this session", "此会话中没有可见的消息", 1),
    ("No messages in this session", "此会话中没有消息", 1),
    ("Invalid wrap offer", "无效的换行建议", 1),
    ("Unknown wrap operation", "未知的换行操作", 1),
    ("User cancelled action.", "用户取消了操作。", 1),
    ("Action returned an error.", "操作返回了错误。", 1),
    ("Missing omnirush.ai affordance id.", "缺少 omnirush.ai 功能入口 id。", 1),
    ("sessionId is required", "必须提供 sessionId。", 8),
    ("title is required", "必须提供 title。", 1),
    ("label is required", "必须提供 label。", 1),
    ("file is required", "必须提供 file。", 1),
    ("workspaceId is required", "必须提供 workspaceId。", 2),
    ("groupId is required", "必须提供 groupId。", 1),
    ("No workspace selected", "未选择工作区", 3),
    ("Could not determine workspace", "无法确定工作区", 1),
    ("Requires confirmed: true", "需要 confirmed: true", 1),
    ("omnirush.ai client is not connected", "omnirush.ai 客户端未连接", 2),
    ("omnirush.ai server is not connected", "omnirush.ai 服务器未连接", 1),
    ("Session was not found in the current session list", "在当前会话列表中未找到该会话", 1),
    ("Workspace runtime is not connected", "工作区运行时未连接", 1),
]

# ---------------------------------------------------------------------------
# RAW: (原始代码片段, 替换片段, i18n 区外预期次数) —— 用于需要上下文的短文案
# ---------------------------------------------------------------------------
RAW = [
    ('children:["Use ",', 'children:["使用 ",', 2),
    ('["Show ",r.appName," preview"]', '["显示 ",r.appName," 预览"]', 1),
    ('["Show ",z," more"]', '["显示另外 ",z," 项"]', 1),
    ('["+",e.models.length-5," more"]', '["+",e.models.length-5," 项"]', 1),
    ('statusLabel:"Signed out"', 'statusLabel:"已退出登录"', 1),
    ('label:"Needs attention"', 'label:"需要处理"', 1),
    ('?"Needs attention":', '?"需要处理":', 1),
    ('statusLabel:"Not checked"', 'statusLabel:"未检查"', 2),
    ('"Save changes":"Save"', '"保存更改":"保存"', 2),
    ('"Save changes":"Save to your dashboard"', '"保存更改":"保存到你的仪表盘"', 1),
    ('submitLabel:"Save changes"', 'submitLabel:"保存更改"', 1),
    ('"Saving\u2026"]', '"保存中\u2026"]', 1),
    ('?"Saving\u2026":R.view.activeRevisionId', '?"保存中\u2026":R.view.activeRevisionId', 1),
    ('o.jsx(sd,{}),"Download"]', 'o.jsx(sd,{}),"下载"]', 1),
    ('{id:"download",label:"Download"', '{id:"download",label:"下载"', 1),
    ('"aria-label":`Set up ${_.name}`', '"aria-label":`设置 ${_.name}`', 1),
]

DELIMS = ['"', "'", "`"]

edits = []
miss = []

for content, trans, expect in T:
    hit = None
    for d in DELIMS:
        # 定界符不能出现在原文或译文中，否则会破坏 JS 字符串
        if d in content or d in trans:
            continue
        a = d + content + d
        occ = occurrences(a)
        if len(occ) == expect:
            hit = (d, a, occ)
            break
    if hit is None:
        best = max((len(occurrences(d + content + d))
                    for d in DELIMS if d not in content and d not in trans),
                   default=-1)
        miss.append((content, expect, best))
        continue
    d, a, occ = hit
    new = d + trans + d
    for i in occ:
        edits.append((i, i + len(a), new))

for raw, new, expect in RAW:
    occ = occurrences(raw)
    if len(occ) != expect:
        miss.append((raw, expect, len(occ)))
        continue
    for i in occ:
        edits.append((i, i + len(raw), new))

if miss:
    print("!! 以下条目未按预期命中：")
    for c, e, g in miss:
        print(f"   预期 {e}，实际 {g}: {c[:100]!r}")
    sys.exit("已中止，未写入")

edits.sort(key=lambda x: x[0], reverse=True)
prev = None
for s, e, _ in edits:
    if prev is not None and e > prev:
        sys.exit(f"!! 区间重叠 @{s}")
    prev = s

out = src
for s, e, new in edits:
    out = out[:s] + new + out[e:]
print(f"共替换 {len(edits)} 处，长度 {orig_len} -> {len(out)} ({len(out)-orig_len:+d})")

tmp = BUNDLE + ".tmpcheck.mjs"
open(tmp, "w", encoding="utf-8", newline="").write(out)
r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
if r.returncode != 0:
    os.remove(tmp)
    sys.exit(f"!! node --check 失败:\n{r.stdout}\n{r.stderr}")
print("node --check \u2713")
os.replace(tmp, BUNDLE)
print(f"已写入 {BUNDLE}")
