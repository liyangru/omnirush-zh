# -*- coding: utf-8 -*-
"""共享：自动探测当前生效的 bundle 路径。

应用每次自动更新都会重写 app-dist/，bundle 文件名带内容 hash（例如
app-CAtSUbH6.js → app-DohXHoBv.js），所有偏移量/备份文件全部作废。
所以这里统一从 index.html 的 <script src> 反查真实文件名，杜绝硬编码。
"""
import os
import re

APP_DIST = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\@omnirushdesktop\resources\app-dist")
ASSETS = os.path.join(APP_DIST, "assets")


def detect_bundle():
    """返回 index.html 实际引用的入口 bundle 绝对路径"""
    html_path = os.path.join(APP_DIST, "index.html")
    if not os.path.exists(html_path):
        raise SystemExit(
            f"!! 找不到 {html_path}\n"
            f"   请确认已安装 OmniRush 桌面版；若安装在别处，\n"
            f"   改 {os.path.abspath(__file__)} 里的 APP_DIST。")
    html = open(html_path, encoding="utf-8").read()
    m = re.search(r'src="\./assets/(app-[A-Za-z0-9_-]+\.js)"', html)
    if not m:
        raise SystemExit(f"!! {html_path} 中找不到 app-*.js 入口引用")
    path = os.path.join(ASSETS, m.group(1))
    if not os.path.exists(path):
        raise SystemExit(f"!! index.html 引用的 bundle 不存在: {path}")
    return path


def bundle_name():
    return os.path.basename(detect_bundle())


BACKUP = None  # 由 backup_path() 惰性计算


def backup_path():
    """当前 bundle 对应的官方原版备份路径"""
    global BACKUP
    if BACKUP is None:
        BACKUP = detect_bundle() + ".orig-backup"
    return BACKUP


if __name__ == "__main__":
    print("当前 bundle:", detect_bundle())
