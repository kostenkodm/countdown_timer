import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import time, os, sys, json
import threading
import pygame
pygame.mixer.init()

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
PRESETS_PATH = os.path.join(CONFIG_DIR, "presets.json")

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
        win = tk.Toplevel(root)
        win.title("Обновление доступно")
        win.geometry("340x160")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.grab_set()
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

class InfoDialog(tk.Toplevel):
    def __init__(self, parent, current_version, latest_version):
        super().__init__(parent)
        self.title("Информация о приложении")
        self.configure(bg="#ffffff")
        self.geometry("360x250")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text="Прозрачный таймер", font=("Segoe UI", 13, "bold"), fg="#333333", bg="#ffffff").pack(pady=(20, 5))
        tk.Label(self, text="Разработчик: Костенко Д.М.", font=("Segoe UI", 10), fg="#555555", bg="#ffffff").pack(pady=2)
        tk.Label(self, text="Репозиторий: github.com/kostenkodm", font=("Segoe UI", 10), fg="#4da6ff", bg="#ffffff", cursor="hand2").pack(pady=2)

        tk.Label(self, text=f"Текущая версия: {current_version}", font=("Segoe UI", 10), fg="#555555", bg="#ffffff").pack(pady=5)
        tk.Label(self, text=f"Доступная версия: {latest_version or 'неизвестно'}", font=("Segoe UI", 10), fg="#555555", bg="#ffffff").pack(pady=(0, 15))

class TransparentTimer:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Управление таймером - {VERSION}")
        self.settings_path = os.path.join(CONFIG_DIR, "settings.json")
        self.position_path = os.path.join(CONFIG_DIR, "position.json")
        self.show_clock = True

        self.time_left = 0
        self.running = False
        self.signal_played = False
        self.signal_file = os.path.join(BASE_DIR, "alarm.wav")
        self.font_size = 33
        self.bg_color = "white"
        self.opacity = 0.8
        self.timer_pos = None
        self.num_plays = 1
        self.sound_enabled = True
        self.presets = {}

        self.load_settings()
        self.load_position()
        self.load_presets()

        self.create_main_window()
        self.create_timer_window()
        self.apply_settings()
        self.update_clock()

    def show_info(self):
        try:
            import requests
            GITHUB_REPO = "https://github.com/kostenkodm/countdown_timer"
            RAW_VERSION_URL = f"{GITHUB_REPO}/raw/main/version.json"
            r = requests.get(RAW_VERSION_URL, timeout=5)
            latest_version = r.json().get("version", "неизвестно") if r.status_code == 200 else "неизвестно"
        except Exception:
            latest_version = "неизвестно"

        InfoDialog(self.root, current_version=VERSION, latest_version=latest_version)

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
                    self.num_plays = data.get("num_plays", 1)
                    self.sound_enabled = data.get("sound_enabled", True)
            except Exception:
                pass

    def save_settings(self):
        data = {
            "signal_file": self.signal_file,
            "font_size": self.font_size,
            "bg_color": self.bg_color,
            "opacity": self.opacity,
            "show_clock": self.show_clock,
            "num_plays": self.num_plays,
            "sound_enabled": self.sound_enabled,
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

    def load_presets(self):
        if os.path.exists(PRESETS_PATH):
            try:
                with open(PRESETS_PATH, "r", encoding="utf-8") as f:
                    self.presets = json.load(f)
            except Exception:
                self.presets = self.get_default_presets()
        else:
            self.presets = self.get_default_presets()

    def save_presets(self):
        with open(PRESETS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.presets, f, indent=2, ensure_ascii=False)

    def get_default_presets(self):
        return {
            "Ларин": {"minutes": 5, "seconds": 0, "font_size": 33, "opacity": 0.8, "bg_color": "white", "num_plays": 1, "sound_enabled": True},
            "Пегов": {"minutes": 3, "seconds": 0, "font_size": 33, "opacity": 0.8, "bg_color": "white", "num_plays": 1, "sound_enabled": True}
        }

    def apply_preset(self, event=None):
        preset_name = self.preset_var.get()
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            self.minutes_entry.delete(0, tk.END)
            self.minutes_entry.insert(0, str(preset.get("minutes", 1)))
            self.seconds_entry.delete(0, tk.END)
            self.seconds_entry.insert(0, str(preset.get("seconds", 0)))
            self.font_scale.set(preset.get("font_size", 33))
            self.opacity_scale.set(preset.get("opacity", 0.8))
            self.bg_var.set("Белый" if preset.get("bg_color", "white") == "white" else "Чёрный")
            self.num_plays_entry.delete(0, tk.END)
            self.num_plays_entry.insert(0, str(preset.get("num_plays", 1)))
            self.sound_var.set(preset.get("sound_enabled", True))
            self.apply_settings()

    def save_new_preset(self):
        name = simpledialog.askstring("Сохранить пресет", "Введите имя пресета:")
        if name:
            preset = {
                "minutes": int(self.minutes_entry.get() or 0),
                "seconds": int(self.seconds_entry.get() or 0),
                "font_size": self.font_size,
                "opacity": self.opacity,
                "bg_color": self.bg_color,
                "num_plays": self.num_plays,
                "sound_enabled": self.sound_enabled
            }
            self.presets[name] = preset
            self.save_presets()
            self.update_preset_menu()

    def delete_preset(self):
        preset_name = self.preset_var.get()
        if preset_name in self.presets:
            del self.presets[preset_name]
            self.save_presets()
            self.update_preset_menu()

    def update_preset_menu(self):
        self.preset_combo['values'] = list(self.presets.keys())
        if self.presets:
            self.preset_var.set(list(self.presets.keys())[0])
        else:
            self.preset_var.set("")

    def create_main_window(self):
        style = ttk.Style()
        style.theme_use('clam')  # Современная тема

        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Проверить обновление", command=check_for_updates)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Действия", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_info)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill="both", expand=True)

        # Блок времени
        time_frame = ttk.LabelFrame(main_frame, text="Время", padding=10)
        time_frame.pack(fill="x", pady=5)

        ttk.Label(time_frame, text="Минуты:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.minutes_entry = ttk.Entry(time_frame, width=8)
        self.minutes_entry.insert(0, "1")
        self.minutes_entry.grid(row=0, column=1, pady=5)

        ttk.Label(time_frame, text="Секунды:").grid(row=0, column=2, padx=10, pady=5, sticky="e")
        self.seconds_entry = ttk.Entry(time_frame, width=8)
        self.seconds_entry.insert(0, "0")
        self.seconds_entry.grid(row=0, column=3, pady=5)

        # Блок визуала
        visual_frame = ttk.LabelFrame(main_frame, text="Визуал", padding=10)
        visual_frame.pack(fill="x", pady=5)

        ttk.Label(visual_frame, text="Размер шрифта:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.font_scale = ttk.Scale(visual_frame, from_=10, to=60, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings())
        self.font_scale.set(self.font_size)
        self.font_scale.grid(row=0, column=1, sticky="we", pady=5)
        self.font_value_label = ttk.Label(visual_frame, text=str(self.font_size), width=4)
        self.font_value_label.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(visual_frame, text="Прозрачность:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.opacity_scale = ttk.Scale(visual_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings())
        self.opacity_scale.set(self.opacity)
        self.opacity_scale.grid(row=1, column=1, sticky="we", pady=5)
        self.opacity_value_label = ttk.Label(visual_frame, text=f"{self.opacity:.2f}", width=4)
        self.opacity_value_label.grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(visual_frame, text="Цвет фона:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.bg_var = tk.StringVar(value="Белый" if self.bg_color == "white" else "Чёрный")
        bg_combo = ttk.Combobox(visual_frame, textvariable=self.bg_var, values=["Белый", "Чёрный"], state="readonly", width=10)
        bg_combo.grid(row=2, column=1, columnspan=2, pady=5, sticky="w")
        bg_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_settings())

        # Блок звука
        sound_frame = ttk.LabelFrame(main_frame, text="Звук", padding=10)
        sound_frame.pack(fill="x", pady=5)

        ttk.Label(sound_frame, text="Кол-во воспр.:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.num_plays_entry = ttk.Entry(sound_frame, width=8)
        self.num_plays_entry.insert(0, str(self.num_plays))
        self.num_plays_entry.grid(row=0, column=1, pady=5)
        self.num_plays_entry.bind("<FocusOut>", lambda e: self.update_num_plays())

        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        ttk.Checkbutton(sound_frame, text="Воспроизводить сигнал", variable=self.sound_var, command=self.toggle_sound).grid(row=1, column=0, columnspan=3, pady=5, sticky="w")

        # Блок пресетов
        preset_frame = ttk.LabelFrame(main_frame, text="Пресеты", padding=10)
        preset_frame.pack(fill="x", pady=5)

        ttk.Label(preset_frame, text="Выбрать:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, state="readonly", width=20)
        self.update_preset_menu()
        self.preset_combo.grid(row=0, column=1, pady=5)
        self.preset_combo.bind("<<ComboboxSelected>>", self.apply_preset)

        preset_button_frame = ttk.Frame(preset_frame)
        preset_button_frame.grid(row=0, column=2, padx=10, pady=5)
        ttk.Button(preset_button_frame, text="Сохранить", command=self.save_new_preset).pack(side="left", padx=5)
        ttk.Button(preset_button_frame, text="Удалить", command=self.delete_preset).pack(side="left", padx=5)

        # Блок кнопок
        button_frame = ttk.Frame(main_frame, padding=10)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(button_frame, text="Старт", command=self.start_timer, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Стоп", command=self.stop_timer, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Сигнал", command=self.choose_signal, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="▶", command=self.play_sound, width=3).pack(side="left", padx=10)

        self.clock_var = tk.BooleanVar(value=self.show_clock)
        ttk.Checkbutton(main_frame, text="Показывать время в покое", variable=self.clock_var, command=self.toggle_clock_mode).pack(anchor="w", pady=5)

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

    def toggle_clock_mode(self):
        self.show_clock = self.clock_var.get()
        self.save_settings()
        self.update_clock()

    def update_clock(self):
        if not self.running and self.time_left == 0:
            if self.show_clock:
                now = time.strftime("%H:%M:%S")
                self.timer_label.config(text=now, fg="gray")
            else:
                self.timer_label.config(text="00:00", fg="gray")
        self.root.after(1000, self.update_clock)

    def start_move(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        x = self.timer_window.winfo_x() + (event.x - self._drag_x)
        y = self.timer_window.winfo_y() + (event.y - self._drag_y)
        self.timer_window.geometry(f"+{x}+{y}")

    def apply_settings(self):
        if not hasattr(self, "timer_window"):
            return

        self.font_size = int(self.font_scale.get())
        self.opacity = float(self.opacity_scale.get())
        self.bg_color = "white" if self.bg_var.get() == "Белый" else "black"

        self.timer_window.attributes("-alpha", self.opacity)
        self.timer_window.config(bg=self.bg_color)
        self.timer_label.config(bg=self.bg_color, font=("Consolas", self.font_size, "bold"))
        self.timer_window.attributes("-transparentcolor", self.bg_color)

        self.font_value_label.config(text=str(self.font_size))
        self.opacity_value_label.config(text=f"{self.opacity:.2f}")

        self.save_settings()

    def start_timer(self):
        try:
            minutes = int(self.minutes_entry.get())
            seconds = int(self.seconds_entry.get())
            self.time_left = minutes * 60 + seconds
            self.update_num_plays()
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
            title="Выберите аудиофайл", filetypes=[("Аудио файлы", "*.wav *.mp3 *.ogg")]
        )
        if file_path:
            self.signal_file = file_path
            self.save_settings()

    def play_sound(self):
        if os.path.exists(self.signal_file):
            try:
                pygame.mixer.Sound(self.signal_file).play()
            except Exception as e:
                messagebox.showwarning("Ошибка", f"Не удалось воспроизвести: {e}")
        else:
            messagebox.showwarning("Ошибка", "Файл не найден!")

    def update_timer(self):
        while self.running and self.time_left >= -300:
            self.update_label()
            if self.time_left == 0 and not self.signal_played:
                if self.sound_enabled and os.path.exists(self.signal_file):
                    sound = pygame.mixer.Sound(self.signal_file)
                    for _ in range(self.num_plays):
                        sound.play()
                        pygame.time.wait(int(sound.get_length() * 1000) + 100)
                self.signal_played = True
            time.sleep(1)
            self.time_left -= 1

        self.running = False
        self.time_left = 0
        self.root.after(0, self.update_clock)

    def update_label(self):
        self.root.after(0, lambda: self._update_label_safe())

    def _update_label_safe(self):
        minutes, seconds = divmod(abs(self.time_left), 60)
        sign = "-" if self.time_left < 0 else ""
        color = "red" if self.time_left < 0 else "green"
        self.timer_label.config(text=f"{sign}{minutes:02d}:{seconds:02d}", fg=color)

    def update_num_plays(self):
        try:
            self.num_plays = int(self.num_plays_entry.get())
            if self.num_plays < 0:
                self.num_plays = 0
        except ValueError:
            self.num_plays = 1
        self.num_plays_entry.delete(0, tk.END)
        self.num_plays_entry.insert(0, str(self.num_plays))
        self.save_settings()

    def toggle_sound(self):
        self.sound_enabled = self.sound_var.get()
        self.save_settings()

if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-topmost", True)  # <- добавляем
    icon_path = os.path.join(BASE_DIR, "icon.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    app = TransparentTimer(root)


    root.after(2000, lambda: threading.Thread(target=lambda: check_for_updates(), daemon=True).start())

    root.mainloop()

    #pyinstaller --onefile --windowed --icon=clock.ico --add-data "alarm.wav;." --add-data "version.json;." timer.py