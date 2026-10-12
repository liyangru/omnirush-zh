# -*- coding: utf-8 -*-
"""检测 OmniRush 的汉化是否还在；不在就自动重打。

应用每次自动更新都会重写 app-dist/，把汉化连同备份一起清掉。
本脚本只做一件事：**发现没汉化就重跑 apply_all2.py**。

可单独运行，也被 autorepatch_watch.py 调用：
    python auto_repatch.py          # 检查并按需重打
    python auto_repatch.py --check  # 只检查，不重打（退出码 0=已汉化 1=未汉化）
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "auto_repatch.log")
LOCK = os.path.join(HERE, "auto_repatch.lock")

# 官方原版约 12,300 汉字；汉化后约 39,000。用 25,000 作分界。
CJK_FLOOR = 25000
# 判定「已汉化」的标记（来自注入的 zh 语言包）
MARKERS = ("压缩此会话以减少上下文大小", "偏好设置")


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def find_node():
    """定位 node.exe —— 写入前要用它做语法校验。"""
    import shutil
    p = shutil.which("node")
    if p:
        return p
    cands = [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\nodejs\node.exe"),
    ]
    # WorkBuddy 自带的 node（可能不在系统 PATH）
    base = os.path.expandvars(r"%USERPROFILE%\.workbuddy-ai\binaries\node\versions")
    if os.path.isdir(base):
        for d in sorted(os.listdir(base), reverse=True):
            cands.append(os.path.join(base, d, "node.exe"))
    for c in cands:
        if os.path.exists(c):
            return c
    return None


def read_bundle(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None


def is_patched(src):
    """src 为 None 表示读不到文件 -> 视为未知（返回 None）。"""
    if src is None:
        return None
    han = sum(1 for c in src if "\u4e00" <= c <= "\u9fff")
    if han < CJK_FLOOR:
        return False
    return any(m in src for m in MARKERS)


def stable_size(path, tries=5, gap=1.0):
    """等文件大小连续两次一致，避免在应用写入途中读取。"""
    last = -1
    for _ in range(tries):
        try:
            cur = os.path.getsize(path)
        except OSError:
            cur = -1
        if cur == last and cur >= 0:
            return cur
        last = cur
        time.sleep(gap)
    return last


def acquire_lock():
    """防止并发重打（监视器与手动运行同时触发）。"""
    if os.path.exists(LOCK):
        try:
            age = time.time() - os.path.getmtime(LOCK)
            if age < 600:      # 10 分钟内的锁视为有效
                return False
            os.remove(LOCK)
        except OSError:
            pass
    try:
        with open(LOCK, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except OSError:
        return False


def release_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def main():
    check_only = "--check" in sys.argv
    quiet = "--quiet" in sys.argv

    sys.path.insert(0, HERE)
    try:
        from _bundle import detect_bundle
        bundle = detect_bundle()
    except SystemExit as e:
        log(f"定位 bundle 失败：{e}")
        return 2
    except Exception as e:  # noqa: BLE001
        log(f"定位 bundle 异常：{type(e).__name__}: {e}")
        return 2

    stable_size(bundle)
    src = read_bundle(bundle)
    patched = is_patched(src)

    if patched:
        if not quiet:
            han = sum(1 for c in src if "\u4e00" <= c <= "\u9fff")
            log(f"已汉化（{os.path.basename(bundle)}，{han:,} 汉字），无需处理")
        return 0

    if patched is None:
        log(f"读不到 bundle：{bundle}")
        return 2

    han = sum(1 for c in src if "\u4e00" <= c <= "\u9fff")
    log(f"检测到未汉化（{os.path.basename(bundle)}，{han:,} 汉字）—— 应用可能刚更新过")
    if check_only:
        return 1

    if not acquire_lock():
        log("另一个重打流程正在进行，跳过本次")
        return 0

    try:
        node = find_node()
        if not node:
            log("!! 找不到 node.exe，无法做语法校验 -> 不重打（请安装 Node.js）")
            return 3
        env = dict(os.environ)
        env["PATH"] = os.path.dirname(node) + os.pathsep + env.get("PATH", "")

        log(f"开始重打补丁（node = {node}）")
        t0 = time.time()
        r = subprocess.run(
            [sys.executable, os.path.join(HERE, "apply_all2.py")],
            cwd=HERE, capture_output=True, text=True, encoding="utf-8",
            errors="replace", env=env,
        )
        out = (r.stdout or "") + (r.stderr or "")
        tail = "\n".join(out.strip().splitlines()[-6:])
        if r.returncode == 0 and "全部完成" in out:
            log(f"重打成功（耗时 {time.time() - t0:.1f}s）")
            log("  输出末尾：" + tail.replace("\n", " | "))
            return 0
        log(f"!! 重打失败（退出码 {r.returncode}）")
        log("  输出末尾：" + tail.replace("\n", " | "))
        return 4
    finally:
        release_lock()


if __name__ == "__main__":
    sys.exit(main())
