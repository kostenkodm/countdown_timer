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
VERSION_FILE = os.path.join(BASE_DIR, "version.json")
try:
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        VERSION = json.load(f).get("version", "0.0.0")
except Exception:
    VERSION = "0.0.0"

CONFIG_DIR = get_config_dir()

# === Проверка обновлений ===
def check_for_updates():
    import requests, zipfile, io, subprocess

    GITHUB_REPO = "https://github.com/kostenkodm/countdown_timer"
    VERSION_FILE = os.path.join(BASE_DIR, "version.json")
    RELEASE_URL = f"{GITHUB_REPO}/releases/latest/download/timer.zip"
    RAW_VERSION_URL = f"{GITHUB_REPO}/raw/main/version.json"

    def get_local_version():
        try:
            with open(VERSION_FILE, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    def get_remote_version():
        try:
            r = requests.get(RAW_VERSION_URL, timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get("version", "0.0.0")
        except Exception:
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
            subprocess.Popen(["update.bat"])
            sys.exit()
        except Exception as e:
            messagebox.showerror("Ошибка обновления", f"Не удалось установить обновление:\n{e}")

    local = get_local_version()
    remote = get_remote_version()

    if is_newer(remote, local):
        # === Создание настоящего модального окна ===
        win = tk.Toplevel(root)
        win.title("Обновление доступно")
        win.geometry("340x160")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.grab_set()  # делает окно модальным
        win.focus_set()

        msg = tk.Label(
            win,
            text=f"Найдена новая версия {remote}\n(текущая {local})",
            justify="center",
            font=("Segoe UI", 10)
        )
        msg.pack(pady=15)

        tk.Label(win, text="Хотите обновить сейчас?", font=("Segoe UI", 9)).pack(pady=5)

        def on_update():
            msg.config(text="Загрузка обновления...")
            for widget in win.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.config(state="disabled")
            root.update()
            download_and_extract()

        def on_cancel():
            win.destroy()

        frame = tk.Frame(win)
        frame.pack(pady=10)
        tk.Button(frame, text="Обновить", command=on_update, width=12).pack(side="left", padx=8)
        tk.Button(frame, text="Позже", command=on_cancel, width=12).pack(side="right", padx=8)
    else:
        print("✅ Используется последняя версия.")

# === Запуск проверки в фоне ===
threading.Thread(target=check_for_updates, daemon=True).start()


class TransparentTimer:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Управление таймером - {VERSION}")
        self.settings_path = os.path.join(CONFIG_DIR, "settings.json")
        self.position_path = os.path.join(CONFIG_DIR, "position.json")
        self.show_clock = True

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
        # Запускаем показ текущего времени, если таймер не активен
        threading.Thread(target=self.show_clock_when_idle, daemon=True).start()

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
                    self.show_clock = data.get("show_clock", True)
            except Exception:
                pass

    def save_settings(self):
        data = {
            "signal_file": self.signal_file,
            "font_size": self.font_size,
            "bg_color": self.bg_color,
            "opacity": self.opacity,
            "show_clock": self.show_clock,
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
        button_frame.grid(row=4, column=0, columnspan=4, pady=(8, 0))

        ttk.Button(button_frame, text="Старт", command=self.start_timer).grid(row=0, column=0, padx=5)
        # ttk.Button(button_frame, text="Пауза", command=self.pause_timer).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Стоп", command=self.stop_timer).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Сигнал", command=self.choose_signal).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="▶", command=self.play_sound, width=3).grid(row=0, column=3, padx=5)
        # Переключатель отображения часов
        self.clock_var = tk.BooleanVar(value=self.show_clock)
        ttk.Checkbutton(
            frame,
            text="Показывать текущее время в покое",
            variable=self.clock_var,
            command=self.toggle_clock_mode
        ).grid(row=5, column=0, columnspan=5, pady=5, sticky="w")

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

    # === Текущее время ===

    def toggle_clock_mode(self):
        self.show_clock = self.clock_var.get()
        self.save_settings()

    def show_clock_when_idle(self):
        while True:
            if not self.running and self.time_left == 0:
                if self.show_clock:
                    now = time.strftime("%H:%M:%S")
                    self.timer_label.config(text=now, fg="gray")
                else:
                    self.timer_label.config(text="00:00", fg="gray")
            time.sleep(1)


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
        self.show_current_time()

    def show_current_time(self):
        now = time.strftime("%H:%M:%S")
        self.timer_label.config(text=now, fg="gray")


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

        # Таймер завершён — возвращаем часы
        self.running = False
        self.time_left = 0
        self.show_current_time()


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

    # Запуск проверки обновлений после загрузки интерфейса
    root.after(2000, lambda: threading.Thread(target=lambda: check_for_updates(), daemon=True).start())

    root.mainloop()


#pyinstaller --onefile --windowed --icon=clock.ico --add-data "alarm.wav;." --add-data "version.json;." --add-data "clock.ico;." timer.py
