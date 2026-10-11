# -*- coding: utf-8 -*-
"""一键重打全部汉化补丁（完全幂等、可复现）。

流水线：
  1. patch_zh.py                        注入补全版 zh 语言包 + 清空白名单 + 默认中文
  2. patch_hardcoded.py                 首页问候语、启动卡片、侧栏、命令面板
  3. scan_remaining.py                  -> remaining_en.json（此时状态 = 1+2）
  4. patch_hardcoded2.py                提供商连接、会话输入区、内置浏览器、应用仪表盘、自动化、设置
  5. scan_remaining.py                  -> remaining_en.json（此时状态 = 1+2+3）
  6. patch_hardcoded3.py                收尾：剩余可见文案
  7. patch_settings.py                  设置总览页（卡片数组 / 标签映射 / 分组标题）
  8. scan_region.py 1194950 5310000     全量扫描 -> remaining2.json
  9. patch_final.py                     收尾：模型选择、命令面板、扩展卡、状态提示
 10. patch_ext.py                       扩展定义区 / 计算机操作面板 / 提供商开关
 11. patch_ui.py                        全量 UI 前端文案清扫（定界符自动识别）
 12. patch_ui2.py                       收尾清扫（开发面板 / 状态映射 / 工具描述）
 13. patch_ui3.py                       提示/错误/空态全量清扫（快照偏移校验）

每层的字符串偏移量都取自「上一层打完」后的扫描结果，因此必须按顺序执行。
第 13 层以 _l9_snapshot.js 为原文基准做逐条校验，确保偏移不会漂移。
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STEPS = [
    ("patch_zh.py", [], "第 1 层 · i18n 语言包"),
    ("patch_hardcoded.py", [], "第 2 层 · 首页/侧栏"),
    ("scan_remaining.py", [], "扫描 · 生成 remaining_en.json"),
    ("patch_hardcoded2.py", [], "第 3 层 · 应用主界面"),
    ("scan_remaining.py", [], "扫描 · 刷新 remaining_en.json"),
    ("patch_hardcoded3.py", [], "第 4 层 · 收尾文案"),
    ("patch_settings.py", [], "第 5 层 · 设置总览页"),
    ("scan_region.py", ["1194950", "5310000"], "扫描 · 生成 remaining2.json"),
    ("patch_final.py", [], "第 6 层 · 模型/命令面板/状态提示"),
    ("patch_ext.py", [], "第 7 层 · 扩展定义/计算机操作面板"),
    ("patch_ui.py", [], "第 8 层 · 全量 UI 文案清扫"),
    ("patch_ui2.py", [], "第 9 层 · 收尾（开发面板/状态/工具描述）"),
    ("patch_ui3.py", [], "第 10 层 · 提示/错误/空态全量清扫"),
]

for script, args, title in STEPS:
    print("=" * 72)
    print(f"### {title}   ({script}{' ' + ' '.join(args) if args else ''})")
    print("=" * 72)
    r = subprocess.run([PY, os.path.join(HERE, script)] + args, cwd=HERE,
                       capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "").rstrip()
    if script.startswith("scan_"):
        keep = [l for l in out.splitlines() if not l.startswith("  [")][:14]
        out = "\n".join(keep)
    print(out)
    if r.returncode != 0:
        print((r.stderr or "").rstrip())
        sys.exit(f"!! {script} 失败")
print("\n全部完成。")
