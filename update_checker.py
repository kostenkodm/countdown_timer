import json, os, sys, urllib.request, shutil, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_URL = "https://raw.githubusercontent.com/kostenkodm/countdown_timer/main/version.json"
UPDATE_SCRIPT = os.path.join(BASE_DIR, "update.bat")
LOCAL_VERSION_FILE = os.path.join(BASE_DIR, "version.json")

def get_local_version():
    if os.path.exists(LOCAL_VERSION_FILE):
        with open(LOCAL_VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("version", "0.0.0")
    return "0.0.0"

def get_remote_version():
    try:
        with urllib.request.urlopen(CONFIG_URL) as r:
            data = json.load(r)
            return data.get("version", "0.0.0")
    except:
        return "0.0.0"

def compare_versions(local, remote):
    return tuple(map(int, remote.split("."))) > tuple(map(int, local.split(".")))

if __name__ == "__main__":
    local = get_local_version()
    remote = get_remote_version()
    if compare_versions(local, remote):
        print(f"Доступна новая версия: {remote} (у вас {local})")
        # Запускаем BAT для обновления
        subprocess.Popen([UPDATE_SCRIPT], shell=True)
    else:
        print(f"Вы используете последнюю версию: {local}")
