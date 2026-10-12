# utils.py
import sys
import os
import json

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- 📍 1번: 위치 저장 / 복원 함수 ---
CONFIG_PATH = os.path.expanduser("~/.cat_widget_config.json")

def save_settings(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"설정 저장 실패: {e}")

def load_settings():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

# --- 📍 2번: 부팅 시 자동 실행 함수 ---
def set_auto_start(enable=True):
    app_path = sys.executable

    if sys.platform == "win32":
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                winreg.SetValueEx(key, "DesktopCatWidget", 0, winreg.REG_SZ, f'"{app_path}"')
            else:
                winreg.DeleteValue(key, "DesktopCatWidget")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Windows failed: {e}")

    elif sys.platform == "darwin":
        plist_path = os.path.expanduser("~/Library/LaunchAgents/com.desktopcat.widget.plist")
        if enable:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.desktopcat.widget</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
            try:
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                with open(plist_path, "w") as f:
                    f.write(plist_content)
            except Exception as e:
                print(f"macOS failed: {e}")