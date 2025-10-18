import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time, threading, winsound, os, sys, json

# === Пути для exe и настроек ===
def get_base_dir():
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_config_dir():
    path = os.path.join(os.getenv("APPDATA"), "TransparentTimer")
    os.makedirs(path, exist_ok=True)
    return path

BASE_DIR = get_base_dir()
CONFIG_DIR = get_config_dir()

# === Проверка обновлений ===
def check_for_updates():
    import requests, zipfile, io, subprocess
    GITHUB_REPO = "https://github.com/kostenkodm/countdown_timer"
    VERSION_FILE = os.path.join(BASE_DIR, "version.json")
    RELEASE_URL = f"{GITHUB_REPO}/releases/latest/download/timer.zip"
    RAW_VERSION_URL = f"{GITHUB_REPO}/raw/main/version.json"

    def get_local_version():
        if os.path.exists(VERSION_FILE):
            try:
                with open(VERSION_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("version", "0.0.0")
            except Exception:
                return "0.0.0"
        return "0.0.0"

    def get_remote_version():
        try:
            r = requests.get(RAW_VERSION_URL, timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get("version", "0.0.0")
        except Exception:
            return "0.0.0"
        return "0.0.0"

    def is_newer(remote, local):
        try:
            return tuple(map(int, remote.split("."))) > tuple(map(int, local.split(".")))
        except Exception:
            return False

    def download_and_extract():
        try:
            r = requests.get(RELEASE_URL, stream=True, timeout=15)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            z.extractall(BASE_DIR)
            print("✅ Обновление загружено.")
            subprocess.Popen(["update.bat"])
            sys.exit()
        except Exception as e:
            print("⚠ Ошибка обновления:", e)

    local = get_local_version()
    remote = get_remote_version()
    if is_newer(remote, local):
        print(f"🔄 Доступно обновление: {local} → {remote}")
        download_and_extract()
    else:
        print("✅ Используется последняя версия.")

# === Запуск проверки в фоне ===
threading.Thread(target=check_for_updates, daemon=True).start()


class TransparentTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление таймером")
        self.settings_path = os.path.join(CONFIG_DIR, "settings.json")
        self.position_path = os.path.join(CONFIG_DIR, "position.json")

        # Значения по умолчанию
        self.time_left = 0
        self.running = False
        self.signal_played = False
        self.signal_file = os.path.join(BASE_DIR, "alarm.wav")
        self.font_size = 33
        self.bg_color = "white"
        self.opacity = 0.8
        self.timer_pos = None

        # Загружаем настройки и позицию
        self.load_settings()
        self.load_position()

        # Создаём интерфейс
        self.create_main_window()
        self.create_timer_window()
        # Настройки применяются только после инициализации интерфейса
        self.apply_settings()

    # === Загрузка и сохранение ===
    def load_settings(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.signal_file = data.get("signal_file", self.signal_file)
                    self.font_size = data.get("font_size", self.font_size)
                    self.bg_color = data.get("bg_color", self.bg_color)
                    self.opacity = data.get("opacity", self.opacity)
            except Exception:
                pass

    def save_settings(self):
        data = {
            "signal_file": self.signal_file,
            "font_size": self.font_size,
            "bg_color": self.bg_color,
            "opacity": self.opacity,
        }
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_position(self):
        if os.path.exists(self.position_path):
            try:
                with open(self.position_path, "r", encoding="utf-8") as f:
                    self.timer_pos = json.load(f)
            except Exception:
                self.timer_pos = None

    def save_position(self):
        try:
            x = self.timer_window.winfo_x()
            y = self.timer_window.winfo_y()
            data = {"x": x, "y": y}
            with open(self.position_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    # === Главное окно ===
    def create_main_window(self):
        frame = ttk.LabelFrame(self.root, text="Настройки таймера", padding=10)
        self.root.attributes("-topmost", True)
        frame.pack(padx=12, pady=12, fill="x")

        # Минуты и секунды
        ttk.Label(frame, text="Минуты:").grid(row=0, column=0, padx=5, pady=3)
        self.minutes_entry = ttk.Entry(frame, width=6)
        self.minutes_entry.insert(0, "1")
        self.minutes_entry.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(frame, text="Секунды:").grid(row=0, column=2, padx=5, pady=3)
        self.seconds_entry = ttk.Entry(frame, width=6)
        self.seconds_entry.insert(0, "0")
        self.seconds_entry.grid(row=0, column=3, padx=5, pady=3)

        # Размер шрифта
        ttk.Label(frame, text="Размер шрифта:").grid(row=1, column=0, padx=5, pady=3)
        self.font_scale = ttk.Scale(
            frame, from_=10, to=60, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings()
        )
        self.font_scale.set(self.font_size)
        self.font_scale.grid(row=1, column=1, columnspan=3, sticky="we", padx=5)

        # Прозрачность
        ttk.Label(frame, text="Прозрачность окна:").grid(row=2, column=0, padx=5, pady=3)
        self.opacity_scale = ttk.Scale(
            frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings()
        )
        self.opacity_scale.set(self.opacity)
        self.opacity_scale.grid(row=2, column=1, columnspan=3, sticky="we", padx=5)

        # Цвет фона
        ttk.Label(frame, text="Цвет фона:").grid(row=3, column=0, padx=5, pady=3)
        self.bg_var = tk.StringVar(value="Белый" if self.bg_color == "white" else "Чёрный")
        bg_combo = ttk.Combobox(
            frame, textvariable=self.bg_var, values=["Белый", "Чёрный"], state="readonly", width=10
        )
        bg_combo.grid(row=3, column=1, columnspan=3, padx=5, pady=3)
        bg_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_settings())

        # Кнопки управления
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=5, pady=(8, 0))

        ttk.Button(button_frame, text="Старт", command=self.start_timer).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Пауза", command=self.pause_timer).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Стоп", command=self.stop_timer).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Сигнал", command=self.choose_signal).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="▶", command=self.play_sound, width=3).grid(row=0, column=4, padx=5)

    # === Окно таймера ===
    def create_timer_window(self):
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.overrideredirect(True)
        self.timer_window.attributes("-topmost", True)
        self.timer_window.attributes("-alpha", self.opacity)

        if self.timer_pos:
            self.timer_window.geometry(f"240x120+{self.timer_pos['x']}+{self.timer_pos['y']}")
        else:
            screen_w = self.timer_window.winfo_screenwidth()
            screen_h = self.timer_window.winfo_screenheight()
            x = screen_w // 2 - 120
            y = screen_h // 2 - 60
            self.timer_window.geometry(f"240x120+{x}+{y}")

        self.timer_label = tk.Label(
            self.timer_window,
            text="00:00",
            font=("Consolas", self.font_size, "bold"),
            fg="green",
            bg=self.bg_color,
        )
        self.timer_label.pack(expand=True, fill="both")

        self.timer_label.bind("<ButtonPress-1>", self.start_move)
        self.timer_label.bind("<B1-Motion>", self.do_move)
        self.timer_label.bind("<ButtonRelease-1>", lambda e: self.save_position())

    # === Перетаскивание ===
    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        x = self.timer_window.winfo_x() + (event.x - self._drag_x)
        y = self.timer_window.winfo_y() + (event.y - self._drag_y)
        self.timer_window.geometry(f"+{x}+{y}")

    # === Настройки применения ===
    def apply_settings(self):
        if not hasattr(self, "timer_window"):
            return  # окно ещё не создано

        self.font_size = int(self.font_scale.get())
        self.opacity = float(self.opacity_scale.get())
        self.bg_color = "white" if self.bg_var.get() == "Белый" else "black"

        self.timer_window.attributes("-alpha", self.opacity)
        self.timer_window.config(bg=self.bg_color)
        self.timer_label.config(bg=self.bg_color, font=("Consolas", self.font_size, "bold"))
        self.timer_window.attributes("-transparentcolor", self.bg_color)

        self.save_settings()

    # === Таймер ===
    def start_timer(self):
        try:
            minutes = int(self.minutes_entry.get())
            seconds = int(self.seconds_entry.get())
            self.time_left = minutes * 60 + seconds
        except ValueError:
            return

        self.signal_played = False
        if not self.running:
            self.running = True
            threading.Thread(target=self.update_timer, daemon=True).start()

    def pause_timer(self):
        self.running = False

    def stop_timer(self):
        self.running = False
        self.time_left = 0
        self.signal_played = False
        self.update_label()

    def choose_signal(self):
        file_path = filedialog.askopenfilename(
            title="Выберите WAV-файл", filetypes=[("WAV файлы", "*.wav")]
        )
        if file_path:
            self.signal_file = file_path
            self.save_settings()

    def play_sound(self):
        if os.path.exists(self.signal_file):
            threading.Thread(
                target=lambda: winsound.PlaySound(self.signal_file, winsound.SND_FILENAME)
            ).start()
        else:
            messagebox.showwarning("Ошибка", "Файл сигнала не найден!")

    def update_timer(self):
        while self.running and self.time_left >= -300:
            self.update_label()
            if self.time_left == 0 and not self.signal_played:
                if os.path.exists(self.signal_file):
                    winsound.PlaySound(self.signal_file, winsound.SND_FILENAME)
                self.signal_played = True
            time.sleep(1)
            self.time_left -= 1
        self.running = False

    def update_label(self):
        minutes, seconds = divmod(abs(self.time_left), 60)
        sign = "-" if self.time_left < 0 else ""
        color = "red" if self.time_left < 0 else "green"
        self.timer_label.config(text=f"{sign}{minutes:02d}:{seconds:02d}", fg=color)


if __name__ == "__main__":
    root = tk.Tk()
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    app = TransparentTimer(root)
    root.mainloop()

#pyinstaller --onefile --windowed --icon=icon.ico --add-data "alarm.wav;." timer.py
