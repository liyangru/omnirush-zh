# -*- coding: utf-8 -*-
"""OmniRush 汉化补丁 · 第四层 —— 收尾：剩余可见文案

覆盖：内置浏览器登录状态、提供商连接卡片、设置→高级诊断说明、
UI 控制 MCP 工具名、终端与校验提示等。
在 patch_hardcoded2.py 之后运行（偏移量来自同一状态下的 remaining_en.json）。
"""
import json, os, subprocess, sys
from _bundle import detect_bundle

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist\assets")
BUNDLE = detect_bundle()
CAND = os.path.join(HERE, "remaining_en.json")

OK_PROPS = {
    "children", "title", "subtitle", "label", "description", "placeholder",
    "hint", "note", "body", "text", "message", "detail", "summary", "caption",
    "heading", "actionLabel", "?", "null",
}

T3 = [
    ("Couldn’t check workspace", "无法检查工作区"),
    ("capability name · arguments · schema digest", "能力名称 · 参数 · schema 摘要"),
    # UI 控制 MCP 的工具名（命令面板 / 工具卡可见）
    ("Type into the composer", "在输入框中输入"),
    ("Send the composer prompt", "发送输入框中的提示词"),
    ("Stop the current run", "停止当前运行"),
    ("Go to the top of the session", "跳到会话顶部"),
    ("Go to the bottom of the session", "跳到会话底部"),
    ("Read the latest session message", "读取最新会话消息"),
    ("Read the current session transcript", "读取当前会话记录"),
    ("Open URL in built-in browser", "在内置浏览器中打开网址"),
    ("Restore browser tab", "恢复浏览器标签页"),
    ("Release browser tab", "释放浏览器标签页"),
    ("Set built-in browser proxy", "设置内置浏览器代理"),
    ("Focus an open session", "聚焦已打开的会话"),
    # 共享 / 提供商
    ("Choose apps to add to a teammate’s dashboard. They must belong to your organization.",
     "选择要添加到队友仪表盘的应用。它们必须属于你的组织。"),
    ("Provider connections", "提供商连接"),
    ("API keys are stored locally on this device. Environment-backed providers must be changed in the worker environment and then reloaded.",
     "API 密钥保存在本设备上。由环境变量提供支持的提供商需在 worker 环境中修改后重新加载。"),
    ("The built-in browser is not signed in to any site.", "内置浏览器尚未登录任何站点。"),
    # 设置 → 高级 / 诊断
    ("Technical details for cloud MCP delivery. Tokens and Authorization headers are redacted before display or copy.",
     "云 MCP 投递的技术详情。令牌和 Authorization 头在显示或复制前已脱敏。"),
    ("Use this when support needs exact runtime state. The main Connect card stays user-facing.",
     "当支持人员需要精确的运行时状态时使用。主“连接”卡片仍面向普通用户。"),
    ("Inspect what the app controls at runtime versus what belongs to your workspace config. This works through the local server and does not require the engine to be healthy.",
     "查看应用在运行时控制哪些内容、哪些属于你的工作区配置。此功能通过本地服务器运行，无需引擎处于健康状态。"),
    ("Shows the runtime database, the injected runtime config, and the workspace-owned engine config files.",
     "显示运行时数据库、注入的运行时配置，以及工作区自有的引擎配置文件。"),
    ("This is the app-built config object requested for the runtime database and injected safely by the server. Sensitive headers are redacted here.",
     "这是应用为运行时数据库构建的配置对象，由服务器安全注入。敏感请求头在此处已脱敏。"),
    ("The engine also reads its own project and global config files. The app injects the runtime config separately; for app-managed keys, the injected config is the source to inspect.",
     "引擎还会读取自己的项目级和全局配置文件。应用单独注入运行时配置；对于由应用管理的键，注入的配置才是应检查的来源。"),
    ("Choose when the app asks before acting, using the icon beside attachments. Off by default. Available with the standard desktop engine.",
     "通过附件旁的图标选择应用在执行前何时询问。默认关闭。需配合标准桌面引擎使用。"),
    ("This switch only shows or hides the control. Hiding it does not reset workspace permissions; choose Workspace defaults in the menu first if you want to remove the override.",
     "此开关仅用于显示或隐藏该控件。隐藏它不会重置工作区权限；如需移除覆盖设置，请先在菜单中选择“工作区默认值”。"),
    ("Engine v1 is the default. Engine v2 (preview) runs as a parallel sidecar with live provider updates and no engine reloads; sessions created on one engine stay in that engine's list.",
     "引擎 v1 为默认。引擎 v2（预览）以并行 sidecar 方式运行，支持提供商实时更新且无需重载引擎；在某个引擎上创建的会话会保留在该引擎的列表中。"),
    ("Refresh makes the agent engine drop its Cloud connection and reconnect from scratch — the engine never retries a failed connection on its own. Diagnostics are redacted before copy.",
     "刷新会让智能体引擎断开 Cloud 连接并从头重新连接——引擎自身绝不会重试失败的连接。诊断信息在复制前已脱敏。"),
    ("Your MCP client starts the UI-control MCP bundled with omnirush.ai over stdio; it discovers the bridge and proxies UI tools to it. It is not an npm package, so never install it with npx.",
     "你的 MCP 客户端通过 stdio 启动 omnirush.ai 内置的 UI 控制 MCP；它会自动发现桥接并把 UI 工具代理给它。它不是 npm 包，因此切勿用 npx 安装。"),
    ("Production discovery file", "生产环境发现文件"),
    ("Dev discovery file", "开发环境发现文件"),
    ("Up to ${pl.maxFiles} files, ${Up(pl.maxFileBytes)} per file, ${Up(pl.maxTotalBytes)} in total. No links or credential files (.env, keys, certificates).",
     "最多 ${pl.maxFiles} 个文件，单个文件不超过 ${Up(pl.maxFileBytes)}，总计不超过 ${Up(pl.maxTotalBytes)}。不接受链接或凭据文件（.env、密钥、证书）。"),
    # 校验提示
    ("Integers must be within the safe integer range.", "整数必须在安全整数范围内。"),
    ("Invalid hostname", "无效的主机名"),
    ("Invalid protocol", "无效的协议"),
]
TRANS = dict(T3)

src = open(BUNDLE, encoding="utf-8").read()
orig_len = len(src)
cands = json.load(open(CAND, encoding="utf-8"))

edits, hit = [], {}
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
    if q in new:
        print(f"  !! 跳过（译文含定界符）：{txt[:50]!r}")
        continue
    if "${" in new and "${" not in txt:
        print(f"  !! 跳过（译文多出模板占位符）：{txt[:50]!r}")
        continue
    edits.append((off + 1, off + 1 + len(txt), new))
    hit[txt] = hit.get(txt, 0) + 1
    miss.discard(txt)

print(f"待替换字面量: {len(edits)} 处，覆盖 {len(hit)} 个不同文案")
if miss:
    print(f"\n未命中（{len(miss)} 条）：")
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
