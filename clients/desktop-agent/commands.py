"""
IRIS AI — Desktop Agent: Command Executor
Cross-platform system commands for macOS, Windows, and Linux.
"""
import os
import sys
import subprocess
import webbrowser
import platform
import psutil
from typing import Optional

SYSTEM = platform.system()  # 'Darwin' | 'Windows' | 'Linux'


# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN / SESSION
# ═══════════════════════════════════════════════════════════════════════════════

def lock_screen():
    if SYSTEM == "Darwin":
        subprocess.run(["pmset", "displaysleepnow"])
    elif SYSTEM == "Windows":
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif SYSTEM == "Linux":
        subprocess.run(["xdg-screensaver", "lock"], check=False)


def sleep_system():
    if SYSTEM == "Darwin":
        subprocess.run(["pmset", "sleepnow"])
    elif SYSTEM == "Windows":
        subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    elif SYSTEM == "Linux":
        subprocess.run(["systemctl", "suspend"], check=False)


def shutdown():
    if SYSTEM == "Darwin":
        subprocess.run(["sudo", "shutdown", "-h", "now"])
    elif SYSTEM == "Windows":
        subprocess.run(["shutdown", "/s", "/t", "0"])
    elif SYSTEM == "Linux":
        subprocess.run(["shutdown", "-h", "now"])


def restart():
    if SYSTEM == "Darwin":
        subprocess.run(["sudo", "shutdown", "-r", "now"])
    elif SYSTEM == "Windows":
        subprocess.run(["shutdown", "/r", "/t", "0"])
    elif SYSTEM == "Linux":
        subprocess.run(["shutdown", "-r", "now"])


# ═══════════════════════════════════════════════════════════════════════════════
# VOLUME
# ═══════════════════════════════════════════════════════════════════════════════

def set_volume(level: int):
    """Set volume 0-100."""
    level = max(0, min(100, level))
    if SYSTEM == "Darwin":
        # osascript sets volume 0-100
        script = f"set volume output volume {level}"
        subprocess.run(["osascript", "-e", script])
    elif SYSTEM == "Windows":
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            import math
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        except ImportError:
            # Fallback using nircmd
            subprocess.run(["nircmd.exe", "setsysvolume", str(int(level * 655.35))])
    elif SYSTEM == "Linux":
        subprocess.run(["amixer", "sset", "Master", f"{level}%"], check=False)


def volume_up(step: int = 10):
    if SYSTEM == "Darwin":
        subprocess.run(["osascript", "-e", f"set volume output volume (output volume of (get volume settings) + {step})"])
    elif SYSTEM == "Linux":
        subprocess.run(["amixer", "sset", "Master", f"{step}%+"], check=False)


def volume_down(step: int = 10):
    if SYSTEM == "Darwin":
        subprocess.run(["osascript", "-e", f"set volume output volume (output volume of (get volume settings) - {step})"])
    elif SYSTEM == "Linux":
        subprocess.run(["amixer", "sset", "Master", f"{step}%-"], check=False)


def mute_volume():
    if SYSTEM == "Darwin":
        subprocess.run(["osascript", "-e", "set volume output muted true"])
    elif SYSTEM == "Linux":
        subprocess.run(["amixer", "set", "Master", "mute"], check=False)


# ═══════════════════════════════════════════════════════════════════════════════
# BRIGHTNESS
# ═══════════════════════════════════════════════════════════════════════════════

def set_brightness(level: int):
    """Set brightness 0-100."""
    level = max(0, min(100, level))
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(level)
    except ImportError:
        print(f"[IRIS] screen_brightness_control not installed, brightness={level} skipped")
    except Exception as e:
        print(f"[IRIS] Brightness error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def open_app(name: str):
    """Open an application by name."""
    if SYSTEM == "Darwin":
        subprocess.Popen(["open", "-a", name])
    elif SYSTEM == "Windows":
        subprocess.Popen(["start", name], shell=True)
    elif SYSTEM == "Linux":
        subprocess.Popen([name.lower()])


def close_app(name: str):
    """Close an application by name."""
    killed = False
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if name.lower() in proc.info["name"].lower():
                proc.kill()
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed


def open_browser(url: str = "https://google.com"):
    """Open URL in default browser."""
    webbrowser.open(url)


# ═══════════════════════════════════════════════════════════════════════════════
# FILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def search_files(query: str, base_dir: Optional[str] = None) -> list[str]:
    """Search for files matching query in home directory."""
    base = base_dir or os.path.expanduser("~")
    matches = []
    query_lower = query.lower()

    for root, dirs, files in os.walk(base):
        # Skip hidden directories and system dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in
                   ("node_modules", "__pycache__", ".git", "Library", "AppData")]
        for f in files:
            if query_lower in f.lower():
                matches.append(os.path.join(root, f))
                if len(matches) >= 20:
                    return matches
    return matches


def open_file(path: str):
    """Open a file with its default application."""
    if SYSTEM == "Darwin":
        subprocess.Popen(["open", path])
    elif SYSTEM == "Windows":
        os.startfile(path)
    elif SYSTEM == "Linux":
        subprocess.Popen(["xdg-open", path])


# ═══════════════════════════════════════════════════════════════════════════════
# AUTOMATION
# ═══════════════════════════════════════════════════════════════════════════════

def type_text(text: str):
    """Type text at current cursor position."""
    try:
        import pyautogui
        pyautogui.write(text, interval=0.02)
    except Exception as e:
        print(f"[IRIS] type_text error: {e}")


def take_screenshot(save_path: Optional[str] = None) -> str:
    """Take a screenshot and save it."""
    try:
        import pyautogui
        path = save_path or os.path.expanduser(f"~/Desktop/iris_screenshot_{int(__import__('time').time())}.png")
        pyautogui.screenshot(path)
        return path
    except Exception as e:
        print(f"[IRIS] Screenshot error: {e}")
        return ""


def send_whatsapp(contact: str, message: str):
    """
    Send a WhatsApp message via WhatsApp Web using pywhatkit.
    Requires WhatsApp Web to be open in the default browser.
    NOTE: This uses desktop automation — WhatsApp Web must be logged in.
    """
    try:
        import pywhatkit
        # immediately=True sends without waiting
        pywhatkit.sendwhatmsg_instantly(contact, message, wait_time=8)
    except ImportError:
        print("[IRIS] pywhatkit not installed. Run: pip install pywhatkit")
    except Exception as e:
        print(f"[IRIS] WhatsApp error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TELEMETRY
# ═══════════════════════════════════════════════════════════════════════════════

def get_telemetry() -> dict:
    """Gather current system telemetry."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    battery = None
    bat = psutil.sensors_battery()
    if bat:
        battery = bat.percent

    # Network (bytes sent/recv since last call — approximate MB/s)
    net = psutil.net_io_counters()

    return {
        "cpu": round(cpu, 1),
        "ram": round(ram, 1),
        "disk": round(disk, 1),
        "battery": round(battery, 1) if battery is not None else None,
        "platform": SYSTEM,
        "platform_version": platform.version()[:50],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMMAND DISPATCHER
# ═══════════════════════════════════════════════════════════════════════════════

def execute_command(command_data: dict) -> dict:
    """
    Main dispatcher. Receives a command dict from the server and executes it.
    Returns a result dict.
    """
    action = command_data.get("action", "")
    params = {k: v for k, v in command_data.items() if k != "action"}

    print(f"[IRIS] Executing: {action} {params}")

    try:
        if action == "lock_screen":          lock_screen()
        elif action == "sleep":              sleep_system()
        elif action == "shutdown":           shutdown()
        elif action == "restart":            restart()
        elif action == "set_volume":         set_volume(params.get("level", 50))
        elif action == "volume_up":          volume_up(params.get("step", 10))
        elif action == "volume_down":        volume_down(params.get("step", 10))
        elif action == "mute":               mute_volume()
        elif action == "set_brightness":     set_brightness(params.get("level", 80))
        elif action == "open_app":           open_app(params.get("name", ""))
        elif action == "close_app":          close_app(params.get("name", ""))
        elif action == "open_browser":       open_browser(params.get("url", "https://google.com"))
        elif action == "search_files":
            results = search_files(params.get("query", ""))
            return {"success": True, "results": results}
        elif action == "open_file":          open_file(params.get("path", ""))
        elif action == "type_text":          type_text(params.get("text", ""))
        elif action == "take_screenshot":
            path = take_screenshot()
            return {"success": True, "path": path}
        elif action == "send_whatsapp":
            send_whatsapp(params.get("contact", ""), params.get("message", ""))
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

        return {"success": True, "action": action}

    except Exception as e:
        print(f"[IRIS] Command error: {e}")
        return {"success": False, "error": str(e), "action": action}
