# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第九层 —— 收尾清扫

覆盖：
  · 开发者性能面板（Cmd+Shift+P / L 浮层）的全部文案
  · 权限/同步状态映射表 uHt
  · 面向用户的剩余提示与错误
  · omnirush.ai 会话/浏览器控制类工具（MCP tool）的 description / hint

与第八层同样的机制：定界符自动识别 + i18n 数据区排除 + 降序写回。
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
    res = []
    i = -1
    while True:
        i = src.find(a, i + 1)
        if i < 0:
            break
        if not (LANG_LO <= i < LANG_HI):
            res.append(i)
    return res


T = [
    # ===== 开发者性能面板（浮层）=====
    ("Reset counters", "重置计数", 1),
    ("Hide (Cmd+Shift+P to toggle)", "隐藏（Cmd+Shift+P 切换）", 1),
    ("No profiler data yet. Interact with the app.", "暂无性能分析数据。请与应用交互。", 1),
    ("Cmd+Shift+P to toggle. Prod builds: off.", "Cmd+Shift+P 切换。生产构建：关闭。", 1),
    ("hottest committed React surfaces", "提交最频繁的 React 界面", 1),
    ("Hide (Cmd+Shift+L to toggle)", "隐藏（Cmd+Shift+L 切换）", 1),
    ("No render samples yet. Interact with the app.", "暂无渲染样本。请与应用交互。", 1),
    ('Cmd+Shift+L toggles. Also available in window.__omnirush.slice("reactRenderWatchdog").',
     'Cmd+Shift+L 切换。也可通过 window.__omnirush.slice("reactRenderWatchdog") 查看。', 1),

    # ===== 剩余用户可见提示 =====
    ("ChatGPT > Account Settings > Security > Enable device code authorization",
     "ChatGPT > 账号设置 > 安全 > 启用设备代码授权", 1),
    ("This action is not available in the current app state.",
     "当前应用状态下无法执行此操作。", 1),
    ("Deletion requires confirmed: true after explicit user confirmation",
     "删除需要在用户明确确认后传入 confirmed: true", 1),
    ("Debug deep links are not wired into the React settings route yet.",
     "调试深链接尚未接入 React 设置路由。", 1),
    ("Unsupported in OmniRush v2 preview", "OmniRush v2 预览版不支持", 1),

    # ===== 工具描述 / 提示 =====
    ("Settings tab: general | ai | preferences | permissions | shell | environment | advanced | appearance | updates | recovery | debug | cloud-account | cloud-providers",
     "设置标签页：general | ai | preferences | permissions | shell | environment | advanced | appearance | updates | recovery | debug | cloud-account | cloud-providers", 1),
    ("Use settings.panel.open for settings such as AI providers, and route.extensions.skills to browse Library.",
     "使用 settings.panel.open 打开诸如 AI 提供商之类的设置，使用 route.extensions.skills 浏览资料库。", 1),
    ("Replace the current session draft and type the supplied text visibly.",
     "替换当前会话草稿，并以可见方式输入所提供的文本。", 1),
    ("Prompt text to place in the composer.", "要放入输入框的提示词文本。", 1),
    ("Send the currently visible composer draft to the active session.",
     "将当前可见的输入框草稿发送到活动会话。", 1),
    ("Stop the current streaming session run.", "停止当前正在流式输出的会话运行。", 1),
    ("Scroll the visible session transcript to the first messages.",
     "将会话记录滚动到最早的消息。", 1),
    ("Scroll the visible session transcript to the newest messages and composer area.",
     "将会话记录滚动到最新的消息和输入框区域。", 1),
    ("Return the latest visible message in the current session transcript.",
     "返回当前会话记录中最新可见的消息。", 1),
    ("Return the last messages from the current session transcript as readable text, including the session ID, title, and message count.",
     "以可读文本形式返回当前会话记录中的最近若干条消息，包括会话 ID、标题和消息数量。", 1),
    ("Number of recent messages to return, from 1 to 30. Defaults to 10.",
     "要返回的最近消息数量，1 到 30。默认为 10。", 1),

    # ===== 内置浏览器类工具 =====
    ("Open a built-in browser tab and return its tab_id and CDP handle. The tab is protected from suspension for its task lifetime until browser.release_tab declares all running and queued browser work complete.",
     "打开一个内置浏览器标签页并返回其 tab_id 和 CDP 句柄。在该标签页的任务生命周期内，直到 browser.release_tab 声明所有运行中和排队的浏览器工作完成为止，它都会受到保护而不会被挂起。", 1),
    ("The website URL to open.", "要打开的网站网址。", 1),
    ("Browser provider. Use builtin or auto. External is reserved for future support.",
     "浏览器提供商。使用 builtin 或 auto；external 预留给未来支持。", 1),
    ("Acquire a fresh protected CDP handle for a tab owned by this conversation. A suspended tab reloads its saved URL, not its previous document, retaining tab_id with a new target_id. A live tab keeps its document. Always use the returned handle. Protection lasts until browser.release_tab.",
     "为属于此对话的标签页获取一个新的受保护 CDP 句柄。被挂起的标签页会重新加载其保存的网址（而非之前的文档），保留 tab_id 但使用新的 target_id；活动中的标签页则保持其文档。请始终使用返回的句柄。保护持续到 browser.release_tab 为止。", 1),
    ("The logical tab_id returned by browser.open_url or browser.restore_tab.",
     "由 browser.open_url 或 browser.restore_tab 返回的逻辑 tab_id。", 1),
    ("Declare all running and queued browser work on this conversation's tab complete and remove its suspension protection. Release does not close, suspend, or invalidate the current target. The user may then manually suspend it. Before starting later browser work, call browser.restore_tab and use its returned protected handle.",
     "声明此对话标签页上所有运行中和排队的浏览器工作均已完成，并移除其防挂起保护。释放不会关闭、挂起或使当前目标失效；之后用户可以手动将其挂起。在开始后续浏览器工作之前，请调用 browser.restore_tab 并使用其返回的受保护句柄。", 1),
    ("The logical tab_id whose browser work is complete.", "浏览器工作已完成的逻辑 tab_id。", 1),
    ("Route all built-in browser traffic through an HTTP/SOCKS proxy (e.g. to browse from another location). Applies to every built-in browser tab until cleared. Pass an empty proxy to restore system network settings.",
     "让所有内置浏览器流量经由 HTTP/SOCKS 代理（例如从其他位置浏览）。在清除之前，适用于每个内置浏览器标签页。传入空代理可恢复系统网络设置。", 1),
    ("Proxy URL like http://user:pass@host:8080 or socks5://host:1080, env:NAME to use the OMNIRUSH_BROWSER_PROXY_NAME environment variable, or empty to clear.",
     "代理网址，例如 http://user:pass@host:8080 或 socks5://host:1080；env:NAME 表示使用 OMNIRUSH_BROWSER_PROXY_NAME 环境变量；留空则清除。", 1),
    ("Focus a session already visible in either split-screen pane, or reuse its existing tab without opening a duplicate.",
     "聚焦已在任一分屏窗格中可见的会话，或复用其现有标签页而不打开重复项。", 1),
    ("Session id from the omnirush.ai context resources or conversation tabs.",
     "来自 omnirush.ai 上下文资源或对话标签页的会话 id。", 1),

    # ===== 会话管理类工具 =====
    ("Return sessions across workspaces. Entries include `pinned`, and pinned sessions come first.",
     "返回跨工作区的会话。条目包含 `pinned`，置顶会话排在前面。", 1),
    ("Focus a visible session or reuse its existing tab. Use list_sessions first to get the session ID.",
     "聚焦可见的会话或复用其现有标签页。请先用 list_sessions 获取会话 ID。", 1),
    ("Session ID from session.list_sessions.", "来自 session.list_sessions 的会话 ID。", 3),
    ("Rename a session by ID. Use list_sessions first to match the title the user said.",
     "按 ID 重命名会话。请先用 list_sessions 匹配用户提到的标题。", 1),
    ("Delete a session by ID. Destructive: only run after explicit user confirmation.",
     "按 ID 删除会话。属于破坏性操作：仅在用户明确确认后执行。", 1),
    ("Must be true after explicit user confirmation.", "必须在用户明确确认后为 true。", 1),
    ("Toggle pin on a session. Pinned sessions appear in a global section at the top of the sidebar.",
     "切换会话的置顶状态。置顶会话显示在侧栏顶部的全局区域中。", 1),
    ("true to archive, false to unarchive.", "true 表示归档，false 表示取消归档。", 1),
    ("Create a new group (folder/separator) in the current workspace sidebar. Sessions can then be moved into it.",
     "在当前工作区侧栏中创建新分组（文件夹/分隔符），之后可以把会话移入其中。", 1),
    ("Assign a session to a group (folder). Pass groupId=null or omit to remove from current group. Use session.group.list to see available groups.",
     "将会话分配到某个分组（文件夹）。传入 groupId=null 或省略则从当前分组移除。使用 session.group.list 查看可用分组。", 1),
    ("Remove a group from the workspace. Sessions in the group become ungrouped (not deleted).",
     "从工作区移除分组。该分组中的会话将变为未分组（不会被删除）。", 1),
]

RAW = [
    ('{policy_off:"Permission off",not_configured:"Not set up",paused:"Paused",syncing:"Syncing",synced:"Synced",error:"Needs attention"}',
     '{policy_off:"权限已关闭",not_configured:"未设置",paused:"已暂停",syncing:"同步中",synced:"已同步",error:"需要处理"}', 1),
]

DELIMS = ['"', "'", "`"]

edits = []
miss = []

for content, trans, expect in T:
    hit = None
    for d in DELIMS:
        if d in content or d in trans:
            continue
        a = d + content + d
        occ = occurrences(a)
        if len(occ) == expect:
            hit = (d, a, occ)
            break
    if hit is None:
        best = max((len(occurrences(d + content + d))
                    for d in DELIMS if d not in content and d not in trans), default=-1)
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
