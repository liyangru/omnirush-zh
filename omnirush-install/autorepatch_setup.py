# -*- coding: utf-8 -*-
"""安装/卸载「OmniRush 汉化自动重打」开机启动项。

实现方式：在 HKCU 的 Run 键下写一条记录，用 pythonw.exe（无控制台窗口）
启动 autorepatch_watch.py。选注册表而不是启动文件夹，是因为注册表值是
UTF-16 存储，中文路径不会出现编码问题。

用法：
    python autorepatch_setup.py --status      # 查看状态
    python autorepatch_setup.py --install     # 安装并立即启动
    python autorepatch_setup.py --uninstall   # 停止并移除
"""
import os
import subprocess
import sys
import time
import winreg

HERE = os.path.dirname(os.path.abspath(__file__))
WATCH = os.path.join(HERE, "autorepatch_watch.py")
BEAT = os.path.join(HERE, "autorepatch_watch.heartbeat")
STOP = os.path.join(HERE, "autorepatch_watch.stop")
LOG = os.path.join(HERE, "autorepatch_watch.log")

RUN_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
ENTRY = "OmniRushZH-AutoRepatch"


def find_pythonw():
    """找一个可用的 pythonw.exe（>=3.8），优先用户自己安装的 Python。"""
    cands = [
        os.path.expandvars(r"%LOCALAPPDATA%\Python\bin\pythonw.exe"),
        os.path.join(os.path.dirname(sys.executable), "pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"),
    ]
    for base in (r"C:\Program Files", r"C:\Program Files (x86)"):
        if os.path.isdir(base):
            for d in sorted(os.listdir(base), reverse=True):
                if d.lower().startswith("python"):
                    cands.append(os.path.join(base, d, "pythonw.exe"))
    for c in cands:
        if not os.path.exists(c):
            continue
        exe = c.replace("pythonw.exe", "python.exe")
        if not os.path.exists(exe):
            continue
        try:
            r = subprocess.run([exe, "-c",
                                "import sys;sys.exit(0 if sys.version_info>=(3,8) else 1)"],
                               capture_output=True, timeout=30)
            if r.returncode == 0:
                return c
        except Exception:  # noqa: BLE001
            continue
    return None


def heartbeat_age():
    try:
        with open(BEAT, encoding="utf-8") as f:
            lines = f.read().split()
        return time.time() - float(lines[1]), int(lines[0])
    except Exception:  # noqa: BLE001
        return None, None


def running():
    age, pid = heartbeat_age()
    if age is None:
        return False, None, None
    return age < 60, age, pid


def current_entry():
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY)
        try:
            v, _ = winreg.QueryValueEx(k, ENTRY)
            return v
        except FileNotFoundError:
            return None
        finally:
            winreg.CloseKey(k)
    except OSError:
        return None


def status():
    print("=" * 68)
    print("OmniRush 汉化自动重打 —— 状态")
    print("=" * 68)
    ent = current_entry()
    print(f"\n[开机启动项] {'已安装' if ent else '未安装'}")
    if ent:
        print(f"  注册表: HKCU\\{RUN_KEY}\\{ENTRY}")
        print(f"  命令  : {ent}")

    ok, age, pid = running()
    if ok:
        print(f"\n[监视器] 运行中（pid {pid}，心跳 {age:.0f} 秒前）")
    elif age is not None:
        print(f"\n[监视器] 心跳过期（{age:.0f} 秒前，pid {pid}）—— 可能已退出")
    else:
        print("\n[监视器] 未运行（没有心跳文件）")

    print(f"\n[日志] {LOG}")
    if os.path.exists(LOG):
        try:
            tail = open(LOG, encoding="utf-8").read().strip().splitlines()[-5:]
            for l in tail:
                print("   " + l)
        except OSError:
            pass
    return 0


def install():
    pyw = find_pythonw()
    if not pyw:
        print("✗ 找不到可用的 pythonw.exe（需要 Python 3.8+）")
        print("  请先安装 Python，然后重跑本命令。")
        return 1
    if not os.path.exists(WATCH):
        print(f"✗ 找不到 {WATCH}")
        return 1

    cmd = f'"{pyw}" "{WATCH}"'
    k = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(k, ENTRY, 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(k)
    print(f"✓ 已写入开机启动项")
    print(f"  {cmd}")

    ok, _, _ = running()
    if ok:
        print("\n监视器已在运行，无需重复启动")
    else:
        # 用 ShellExecuteW 交给系统外壳启动，比 Popen 脱离得更彻底
        # （不会成为当前终端的子进程，终端关掉也不受影响）
        import ctypes
        import ctypes.wintypes as wt
        shell32 = ctypes.windll.shell32
        shell32.ShellExecuteW.argtypes = [wt.HWND, wt.LPCWSTR, wt.LPCWSTR,
                                          wt.LPCWSTR, wt.LPCWSTR, ctypes.c_int]
        shell32.ShellExecuteW.restype = ctypes.c_void_p
        r = shell32.ShellExecuteW(None, "open", pyw, f'"{WATCH}"', HERE, 0)
        print(f"\n已请求启动监视器（ShellExecuteW 返回 {r}），等待心跳...")
        for _ in range(20):
            time.sleep(1)
            ok, age, pid = running()
            if ok:
                print(f"✓ 监视器运行中（pid {pid}）")
                break
        else:
            print("⚠ 未收到心跳，请检查 autorepatch_watch.log")
    print("\n完成后可运行：python autorepatch_setup.py --status")
    return 0


def uninstall():
    removed = False
    try:
        k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(k, ENTRY)
            removed = True
        except FileNotFoundError:
            pass
        winreg.CloseKey(k)
    except OSError as e:
        print("删除注册表项失败:", e)
    print("✓ 已移除开机启动项" if removed else "（开机启动项本来就不存在）")

    ok, age, pid = running()
    if ok:
        with open(STOP, "w", encoding="utf-8") as f:
            f.write("stop\n")
        print("已放置停止标记，等待监视器退出...")
        for _ in range(20):
            time.sleep(1)
            ok, age, pid = running()
            if not ok:
                print("✓ 监视器已退出")
                break
        else:
            print(f"⚠ 监视器仍在运行（pid {pid}），可手动结束该 pythonw 进程")
    else:
        print("（监视器未在运行）")
    return 0


if __name__ == "__main__":
    if "--install" in sys.argv:
        sys.exit(install())
    if "--uninstall" in sys.argv:
        sys.exit(uninstall())
    sys.exit(status())
