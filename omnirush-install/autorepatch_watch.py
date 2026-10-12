# -*- coding: utf-8 -*-
"""常驻轻量监视器：OmniRush 被自动更新后，自动把汉化补丁打回去。

为什么需要它
------------
OmniRush 会自动下载并安装更新，安装时会**整体重写** resources/app-dist/，
把汉化连同 .orig-backup 一起清掉。这个进程负责发现并修复。

工作方式
--------
每 INTERVAL 秒对当前 bundle 做一次 stat（开销可忽略，不读文件内容）。
只有「路径/大小/修改时间」任一变化时，才去读文件判断是否已汉化；
未汉化则调用 apply_all2.py 重打。

退出：在脚本同目录建一个 autorepatch_watch.stop 文件即可。
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

INTERVAL = 20            # 秒
STOP = os.path.join(HERE, "autorepatch_watch.stop")
LOG = os.path.join(HERE, "autorepatch_watch.log")
BEAT = os.path.join(HERE, "autorepatch_watch.heartbeat")
MAX_LOG = 1_000_000      # 日志超过 1 MB 就截断重来

import auto_repatch as ar  # noqa: E402


def heartbeat():
    """写心跳（pid + 时间戳），供 autorepatch_setup.py --status 判断是否在跑。"""
    try:
        with open(BEAT, "w", encoding="utf-8") as f:
            f.write(f"{os.getpid()}\n{time.time()}\n")
    except OSError:
        pass


def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > MAX_LOG:
            os.replace(LOG, LOG + ".old")
    except OSError:
        pass
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def signature(bundle):
    st = os.stat(bundle)
    return (bundle, st.st_size, st.st_mtime_ns)


def main():
    # --iterations N：只跑 N 轮就退出，用于手动验证/自检
    max_iter = None
    for i, a in enumerate(sys.argv):
        if a == "--iterations" and i + 1 < len(sys.argv):
            try:
                max_iter = int(sys.argv[i + 1])
            except ValueError:
                pass
    log(f"监视器启动（pid {os.getpid()}，间隔 {INTERVAL}s"
        + (f"，仅跑 {max_iter} 轮" if max_iter else "") + "）")
    last = None
    fails = 0
    rounds = 0
    while True:
        rounds += 1
        if max_iter and rounds > max_iter:
            log(f"已达 {max_iter} 轮，退出")
            try:
                os.remove(BEAT)
            except OSError:
                pass
            return 0
        heartbeat()
        if os.path.exists(STOP):
            log("检测到 stop 文件，退出")
            try:
                os.remove(STOP)
            except OSError:
                pass
            try:
                os.remove(BEAT)
            except OSError:
                pass
            return 0
        try:
            from _bundle import detect_bundle
            bundle = detect_bundle()
            sig = signature(bundle)
            if sig != last:
                ar.stable_size(bundle)
                src = ar.read_bundle(bundle)
                patched = ar.is_patched(src)
                if patched is None:
                    log("bundle 暂时读不到（可能正在写入），稍后重试")
                elif patched:
                    log(f"已汉化：{os.path.basename(bundle)}")
                    last = signature(bundle)
                else:
                    han = sum(1 for c in (src or "") if "\u4e00" <= c <= "\u9fff")
                    log(f"发现未汉化（{os.path.basename(bundle)}，{han:,} 汉字）—— 开始重打")
                    rc = ar.main()
                    if rc == 0:
                        log("重打完成")
                        fails = 0
                    else:
                        fails += 1
                        log(f"重打返回 {rc}（连续失败 {fails} 次）")
                    try:
                        last = signature(bundle)
                    except OSError:
                        last = None
        except SystemExit as e:
            # detect_bundle 在应用更新中途会找不到 index.html
            log(f"暂时无法定位 bundle（{e}），稍后重试")
        except Exception as e:  # noqa: BLE001
            log(f"循环异常：{type(e).__name__}: {e}")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    # pythonw.exe 没有控制台，未捕获的异常会静默消失 —— 全部落盘到日志
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as e:  # noqa: BLE001
        import traceback
        try:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"!! 未捕获异常，进程退出\n{traceback.format_exc()}\n")
        except OSError:
            pass
        sys.exit(1)
