# -*- coding: utf-8 -*-
"""验证第二层补丁：截图中的英文串是否已替换为中文，且无残留。"""
import os, re
from _bundle import detect_bundle

B = detect_bundle()  # noqa
s = open(B, encoding="utf-8").read()

MUST_GONE = [
    'children:"Audit trail"',
    'children:"Workflows"',
    'children:"Settings"',
    'title:"what would you like to work on?"',
    'subtitle:"describe the outcome you need"',
    'title:"Fix a hard bug"',
    'title:"Make it faster"',
    'title:"Fix the build"',
    'title:"Refactor or migrate"',
    'title:"Build a real feature"',
    'title:"Systems work"',
    '"sign in to omnirush.ai"',
    '"Sign in again to continue"',
    'label:"Workflows"',
    '"Workflows & model routing"',
    'label:"Run history"',
    'label:"Model routing"',
    '"Audit trail has a failure"',
    '"Audit trail is waiting for approval"',
    'tooltip:"Settings"',
    '"Organization prompt 1"',
    '{recent:"Recent",actions:"Actions"',
    'breadcrumb:"Settings"',
]

MUST_PRESENT = [
    'children:"审计日志"',
    'children:"工作流"',
    'children:"设置"',
    '你想做什么？',
    '描述你期望的结果',
    'title:"修复疑难 Bug"',
    'title:"提升性能"',
    'title:"修复构建"',
    'title:"重构或迁移"',
    'title:"实现完整功能"',
    'title:"系统层工作"',
    '"登录 omnirush.ai"',
    '"请重新登录以继续"',
    'label:"工作流"',
    '"工作流与模型路由"',
    'label:"运行历史"',
    'label:"模型路由"',
    'tooltip:"设置"',
    '组织提示词 1',
    '{recent:"最近",actions:"操作"',
    'breadcrumb:"设置"',
    '审计日志存在失败记录',
    '早上好，我能帮上什么忙？',
    '复现问题、定位根因、修复并验证',
]

print("=== 截图中英文串是否已消失 ===")
bad = 0
for m in MUST_GONE:
    c = s.count(m)
    print(f"  {'✓' if c == 0 else '✗'} {c:>3}  {m}")
    bad += 1 if c else 0

print("\n=== 中文串是否已就位 ===")
miss = 0
for m in MUST_PRESENT:
    c = s.count(m)
    print(f"  {'✓' if c > 0 else '✗'} {c:>3}  {m}")
    miss += 0 if c else 1

# i18n 数据区仍应完好
lang_lo = s.find('"account.mcp_connected_one"')
lang_hi = s.find(";function Ws(", lang_lo)
seg = s[lang_lo:lang_hi]
print("\n=== i18n 数据区完好性 ===")
print(f"  区间 [{lang_lo}, {lang_hi}]  长度 {len(seg):,}")
for probe in ['"settings.tab_general":"Settings"', '"status.settings":"Settings"',
              '"common.save":"', '"app.compact_command_desc":"']:
    print(f"  {'✓' if probe in seg else '✗'} {probe}")

print(f"\n残留英文串: {bad} | 缺失中文串: {miss}")
