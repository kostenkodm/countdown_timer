import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter.font as tkfont
import time, os, sys, json, hashlib, requests, zipfile, io, subprocess, threading, shutil
import pygame

# Инициализация Pygame для воспроизведения звука
pygame.mixer.init()

# === Пути для exe и настроек ===

def get_base_dir():
    """Возвращает базовую директорию приложения (для PyInstaller или локального запуска)."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_config_dir():
    """Создаёт и возвращает директорию для хранения конфигураций в %APPDATA%."""
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

def check_for_updates(parent):
    """Проверяет наличие обновлений на GitHub, предлагает установить с прогрессом и проверкой хеша."""
    GITHUB_REPO = "https://github.com/kostenkodm/countdown_timer"
    VERSION_FILE = os.path.join(BASE_DIR, "version.json")
    RELEASE_URL = f"{GITHUB_REPO}/releases/latest/download/timer.zip"
    HASH_URL = f"{GITHUB_REPO}/releases/latest/download/sha256sum.txt"
    RAW_VERSION_URL = f"{GITHUB_REPO}/raw/main/version.json"

    def get_local_version():
        """Получает локальную версию из version.json."""
        try:
            with open(VERSION_FILE, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    def get_remote_version():
        """Получает удалённую версию из GitHub."""
        try:
            r = requests.get(RAW_VERSION_URL, timeout=5)
            if r.status_code == 200:
                data = r.json()
                return data.get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    def is_newer(remote, local):
        """Сравнивает версии, возвращает True, если удалённая новее."""
        try:
            return tuple(map(int, remote.split("."))) > tuple(map(int, local.split(".")))
        except Exception:
            return False

    def compute_sha256(file_path):
        """Вычисляет SHA256-хеш файла."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def download_and_update():
        """Скачивает, проверяет и устанавливает обновление."""
        try:
            # Получаем хеш
            r_hash = requests.get(HASH_URL, timeout=5)
            if r_hash.status_code != 200:
                messagebox.showerror("Ошибка", "Не удалось получить хеш обновления.")
                return
            expected_hash = r_hash.text.strip().split()[0]

            # Создаём временную папку
            temp_dir = os.path.join(CONFIG_DIR, "temp_update")
            os.makedirs(temp_dir, exist_ok=True)
            zip_path = os.path.join(temp_dir, "timer.zip")

            # Загрузка с прогрессом
            r = requests.get(RELEASE_URL, stream=True, timeout=15)
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / total_size) * 100
                        progress_var.set(f"Загрузка: {progress:.1f}%")
                        parent.update()

            # Проверка хеша
            actual_hash = compute_sha256(zip_path)
            if actual_hash != expected_hash:
                messagebox.showerror("Ошибка", "Хеш-сумма не совпадает, обновление повреждено.")
                return

            # Резервное копирование
            backup_dir = os.path.join(CONFIG_DIR, "backup")
            os.makedirs(backup_dir, exist_ok=True)
            current_exe = os.path.join(BASE_DIR, "timer.exe")
            if os.path.exists(current_exe):
                shutil.copy2(current_exe, os.path.join(backup_dir, f"timer_backup_{VERSION}.exe"))

            # Распаковка
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(BASE_DIR)

            # Очистка
            shutil.rmtree(temp_dir, ignore_errors=True)

            # Перезапуск
            messagebox.showinfo("Успех", "Обновление установлено. Приложение будет перезапущено.")
            subprocess.Popen([os.path.join(BASE_DIR, "timer.exe")])
            sys.exit()

        except Exception as e:
            messagebox.showerror("Ошибка обновления", f"Не удалось установить обновление:\n{e}")

    local = get_local_version()
    remote = get_remote_version()

    if is_newer(remote, local):
        win = tk.Toplevel(parent)
        win.title("Обновление доступно")
        win.geometry("340x200")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.grab_set()
        win.focus_set()

        tk.Label(
            win,
            text=f"Найдена новая версия {remote}\n(текущая {local})",
            justify="center",
            font=("Segoe UI", 10)
        ).pack(pady=10)

        tk.Label(win, text="Хотите обновить сейчас?", font=("Segoe UI", 9)).pack(pady=5)

        progress_var = tk.StringVar(value="Ожидание...")
        tk.Label(win, textvariable=progress_var, font=("Segoe UI", 9)).pack(pady=5)

        def on_update():
            threading.Thread(target=download_and_update, daemon=True).start()

        def on_cancel():
            win.destroy()

        frame = tk.Frame(win)
        frame.pack(pady=5)
        tk.Button(frame, text="Обновить", command=on_update, width=12).pack(side="left", padx=8)
        tk.Button(frame, text="Позже", command=on_cancel, width=12).pack(side="right", padx=8)
    else:
        print("✅ Используется последняя версия.")

class InfoDialog(tk.Toplevel):
    """Окно с информацией о приложении."""
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
    """Основной класс приложения TransparentTimer."""
    def __init__(self, root):
        self.root = root
        self.root.title(f"Управление таймером - {VERSION}")
        self.root.attributes("-topmost", True)  # Окно настроек всегда поверх остальных
        self.settings_path = os.path.join(CONFIG_DIR, "settings.json")
        self.position_path = os.path.join(CONFIG_DIR, "position.json")
        self.show_clock = True
        self.show_progress = True  # Показывать прогресс-бар

        # Инициализация переменных
        self.time_left = 0
        self.initial_time = 0  # Начальное время для прогресс-бара
        self.running = False
        self.signal_played = False
        self.signal_file = os.path.join(BASE_DIR, "alarm.wav")
        self.font_size = 33
        self.font_family = "Consolas"
        self.font_weight = "bold"
        self.bg_color = "white"
        self.opacity = 0.8
        self.fg_positive = "#00FF00"  # Цвет текста для времени > 0
        self.fg_negative = "#FF0000"  # Цвет текста для времени < 0
        self.fg_idle = "#808080"      # Цвет текста для состояния покоя
        self.timer_pos = None
        self.num_plays = 1
        self.sound_enabled = True
        self.presets = {}
        self.theme_name = "flatly"

        # Настройка стиля для тонкого прогресс-бара
        self.style = ttk.Style()
        self.style.configure("ThinProgressBar.TProgressbar", thickness=5)

        # Загрузка настроек и применение темы
        self.load_settings()
        try:
            self.root.style.theme_use(self.theme_name)
        except Exception:
            self.theme_name = "flatly"
            self.root.style.theme_use(self.theme_name)
        self.load_position()
        self.load_presets()
        self.create_main_window()
        self.create_timer_window()
        self.apply_settings()
        self.update_clock()

    def show_info(self):
        """Показывает окно с информацией о приложении."""
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
        """Загружает настройки из settings.json."""
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.signal_file = data.get("signal_file", self.signal_file)
                    self.font_size = data.get("font_size", self.font_size)
                    self.font_family = data.get("font_family", "Consolas")
                    self.font_weight = data.get("font_weight", "bold")
                    self.bg_color = data.get("bg_color", self.bg_color)
                    self.opacity = data.get("opacity", self.opacity)
                    self.fg_positive = data.get("fg_positive", "#00FF00")
                    self.fg_negative = data.get("fg_negative", "#FF0000")
                    self.fg_idle = data.get("fg_idle", "#808080")
                    self.show_clock = data.get("show_clock", True)
                    self.show_progress = data.get("show_progress", False)
                    self.num_plays = data.get("num_plays", 1)
                    self.sound_enabled = data.get("sound_enabled", True)
                    self.theme_name = data.get("theme_name", "flatly")
            except Exception:
                pass

    def save_settings(self):
        """Сохраняет настройки в settings.json."""
        data = {
            "signal_file": self.signal_file,
            "font_size": self.font_size,
            "font_family": self.font_family,
            "font_weight": self.font_weight,
            "bg_color": self.bg_color,
            "opacity": self.opacity,
            "fg_positive": self.fg_positive,
            "fg_negative": self.fg_negative,
            "fg_idle": self.fg_idle,
            "show_clock": self.show_clock,
            "show_progress": self.show_progress,
            "num_plays": self.num_plays,
            "sound_enabled": self.sound_enabled,
            "theme_name": self.theme_name,
        }
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_position(self):
        """Загружает позицию таймера из position.json."""
        if os.path.exists(self.position_path):
            try:
                with open(self.position_path, "r", encoding="utf-8") as f:
                    self.timer_pos = json.load(f)
            except Exception:
                self.timer_pos = None

    def save_position(self):
        """Сохраняет позицию таймера в position.json."""
        try:
            x = self.timer_window.winfo_x()
            y = self.timer_window.winfo_y()
            data = {"x": x, "y": y}
            with open(self.position_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def reset_timer_position(self):
        """Сбрасывает позицию окна таймера в центр экрана."""
        screen_w = self.timer_window.winfo_screenwidth()
        screen_h = self.timer_window.winfo_screenheight()
        x = screen_w // 2 - 150  # Центрируем для ширины 300
        y = screen_h // 2 - 40   # Центрируем для высоты 80
        self.timer_window.geometry(f"300x80+{x}+{y}")
        self.timer_pos = {"x": x, "y": y}
        self.save_position()

    def load_presets(self):
        """Загружает пресеты из presets.json или использует дефолтные."""
        if os.path.exists(PRESETS_PATH):
            try:
                with open(PRESETS_PATH, "r", encoding="utf-8") as f:
                    self.presets = json.load(f)
            except Exception:
                self.presets = self.get_default_presets()
        else:
            self.presets = self.get_default_presets()

    def save_presets(self):
        """Сохраняет пресеты в presets.json."""
        with open(PRESETS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.presets, f, indent=2, ensure_ascii=False)

    def get_default_presets(self):
        """Возвращает стандартные пресеты."""
        return {
            "Ларин": {"minutes": 5, "seconds": 0, "font_size": 33, "opacity": 0.8, "bg_color": "white", "num_plays": 1, "sound_enabled": True},
            "Пегов": {"minutes": 3, "seconds": 0, "font_size": 33, "opacity": 0.8, "bg_color": "white", "num_plays": 1, "sound_enabled": True}
        }

    def apply_preset(self, event=None):
        """Применяет выбранный пресет."""
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
        """Сохраняет новый пресет."""
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
        """Удаляет выбранный пресет."""
        preset_name = self.preset_var.get()
        if preset_name in self.presets:
            del self.presets[preset_name]
            self.save_presets()
            self.update_preset_menu()

    def update_preset_menu(self):
        """Обновляет выпадающее меню пресетов."""
        self.preset_combo['values'] = list(self.presets.keys())
        if self.presets:
            self.preset_var.set(list(self.presets.keys())[0])
        else:
            self.preset_var.set("")

    def open_theme_selection(self):
        """Открывает модальное окно для выбора темы, шрифта и цветов."""
        theme_win = tk.Toplevel(self.root)
        theme_win.title("Настройки темы и шрифта")
        theme_win.geometry("300x340")
        theme_win.resizable(False, False)
        theme_win.attributes("-topmost", True)
        theme_win.grab_set()
        theme_win.focus_set()

        # Выбор темы
        ttk.Label(theme_win, text="Выберите тему:").pack(pady=5)
        theme_var = tk.StringVar(value=self.theme_name)
        theme_combo = ttk.Combobox(theme_win, textvariable=theme_var, values=[
            "darkly", "flatly", "cyborg", "litera", "minty", "morph", "pulse", "sandstone",
            "simplex", "solar", "superhero", "united", "vapor", "yeti"
        ], state="readonly")
        theme_combo.pack(pady=5)
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.change_theme(theme_var.get()))

        # Выбор шрифта
        ttk.Label(theme_win, text="Выберите шрифт:").pack(pady=5)
        font_frame = ttk.Frame(theme_win)
        font_frame.pack(pady=5, fill="x", padx=10)
        self.font_var = tk.StringVar(value=self.font_family)
        font_combo = ttk.Combobox(font_frame, textvariable=self.font_var, values=["Consolas", "Arial", "Courier New", "Times New Roman"], state="readonly")
        font_combo.pack(side="left", fill="x", expand=True)
        font_combo.bind("<<ComboboxSelected>>", lambda e: self.change_font(self.font_var.get(), self.font_weight))
        ttk.Button(font_frame, text="...", command=self.open_font_dialog, width=3).pack(side="left", padx=5)

        # Выбор цветов
        ttk.Label(theme_win, text="Цвета текста таймера:").pack(pady=5)
        color_frame = ttk.Frame(theme_win)
        color_frame.pack(pady=5, fill="x", padx=10)
        ttk.Button(color_frame, text="Больше 0", command=lambda: self.choose_color("positive")).pack(fill="x", pady=2)
        ttk.Button(color_frame, text="Меньше 0", command=lambda: self.choose_color("negative")).pack(fill="x", pady=2)
        ttk.Button(color_frame, text="Часы", command=lambda: self.choose_color("idle")).pack(fill="x", pady=2)

    def choose_color(self, color_type):
        """Открывает диалог выбора цвета для текста таймера."""
        initial_color = getattr(self, f"fg_{color_type}")
        color = colorchooser.askcolor(initialcolor=initial_color, title=f"Выберите цвет ({color_type})")
        if color[1]:  # color[1] содержит HEX-значение
            if color_type == "positive":
                self.fg_positive = color[1]
            elif color_type == "negative":
                self.fg_negative = color[1]
            elif color_type == "idle":
                self.fg_idle = color[1]
            self.apply_settings()
            self.save_settings()

    def open_font_dialog(self):
        """Открывает диалог выбора шрифта."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор шрифта")
        dialog.geometry("300x240")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ttk.Label(dialog, text="Семейство шрифта:").pack(pady=5)
        font_families = sorted(list(tkfont.families()))  # Сортировка для удобства
        font_family_var = tk.StringVar(value=self.font_family)
        font_combo = ttk.Combobox(dialog, textvariable=font_family_var, values=font_families, state="readonly")
        font_combo.pack(pady=5, fill="x", padx=10)

        ttk.Label(dialog, text="Стиль шрифта:").pack(pady=5)
        font_weight_var = tk.StringVar(value=self.font_weight)
        weight_combo = ttk.Combobox(dialog, textvariable=font_weight_var, values=["normal", "bold"], state="readonly")
        weight_combo.pack(pady=5, fill="x", padx=10)

        def apply_font():
            self.change_font(font_family_var.get(), font_weight_var.get())
            dialog.destroy()

        ttk.Button(dialog, text="Применить", command=apply_font).pack(pady=10)

    def change_theme(self, new_theme):
        """Меняет тему на лету и сохраняет."""
        self.theme_name = new_theme
        try:
            self.root.style.theme_use(self.theme_name)
            # Обновляем стиль прогресс-бара
            if hasattr(self, "progress_bar"):
                color = self.fg_positive if self.time_left > 0 else self.fg_negative if self.time_left < 0 else self.fg_idle
                self.style.configure("ThinProgressBar.TProgressbar", background=color)
        except Exception:
            self.theme_name = "flatly"
            self.root.style.theme_use(self.theme_name)
        self.apply_settings()
        self.save_settings()

    def change_font(self, new_font, new_weight):
        """Меняет шрифт таймера на лету и сохраняет."""
        self.font_family = new_font
        self.font_weight = new_weight
        self.apply_settings()
        self.save_settings()

    def toggle_progress_bar(self):
        """Включает/выключает прогресс-бар."""
        self.show_progress = self.progress_var.get()
        if self.show_progress:
            self.progress_bar.pack(fill="x", padx=5, pady=2)
        else:
            self.progress_bar.pack_forget()
        self.save_settings()

    def create_main_window(self):
        """Создаёт главное окно с современной темой и уменьшенными вертикальными отступами."""
        # Меню
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Выбор темы и шрифта", command=self.open_theme_selection)
        settings_menu.add_separator()
        settings_menu.add_command(label="Проверить обновление", command=lambda: check_for_updates(self.root))
        settings_menu.add_separator()
        settings_menu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Настройки", menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_info)
        menubar.add_cascade(label="Справка", menu=help_menu)
        self.root.config(menu=menubar)

        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.pack(fill="both", expand=True)

        # Блок времени
        time_frame = ttk.LabelFrame(main_frame, text="Время", padding=5)
        time_frame.pack(fill="x", pady=3)
        ttk.Label(time_frame, text="Минуты:").grid(row=0, column=0, padx=10, pady=3, sticky="e")
        self.minutes_entry = ttk.Entry(time_frame, width=8)
        self.minutes_entry.insert(0, "3")
        self.minutes_entry.grid(row=0, column=1, pady=3)
        ttk.Label(time_frame, text="Секунды:").grid(row=0, column=2, padx=10, pady=3, sticky="e")
        self.seconds_entry = ttk.Entry(time_frame, width=8)
        self.seconds_entry.insert(0, "0")
        self.seconds_entry.grid(row=0, column=3, pady=3)

        # Блок визуала
        visual_frame = ttk.LabelFrame(main_frame, text="Визуал", padding=5)
        visual_frame.pack(fill="x", pady=3)
        ttk.Label(visual_frame, text="Размер шрифта:").grid(row=0, column=0, padx=10, pady=3, sticky="e")
        self.font_scale = ttk.Scale(visual_frame, from_=10, to=60, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings())
        self.font_scale.set(self.font_size)
        self.font_scale.grid(row=0, column=1, sticky="we", pady=3)
        self.font_value_label = ttk.Label(visual_frame, text=str(self.font_size), width=4)
        self.font_value_label.grid(row=0, column=2, padx=5, pady=3)
        ttk.Label(visual_frame, text="Прозрачность:").grid(row=1, column=0, padx=10, pady=3, sticky="e")
        self.opacity_scale = ttk.Scale(visual_frame, from_=0.1, to=1.0, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings())
        self.opacity_scale.set(self.opacity)
        self.opacity_scale.grid(row=1, column=1, sticky="we", pady=3)
        self.opacity_value_label = ttk.Label(visual_frame, text=f"{self.opacity:.2f}", width=4)
        self.opacity_value_label.grid(row=1, column=2, padx=5, pady=3)
        ttk.Label(visual_frame, text="Цвет фона:").grid(row=2, column=0, padx=10, pady=3, sticky="e")
        self.bg_var = tk.StringVar(value="Белый" if self.bg_color == "white" else "Чёрный")
        bg_combo = ttk.Combobox(visual_frame, textvariable=self.bg_var, values=["Белый", "Чёрный"], state="readonly", width=10)
        bg_combo.grid(row=2, column=1, columnspan=2, pady=3, sticky="w")
        bg_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_settings())

        # Блок звука
        sound_frame = ttk.LabelFrame(main_frame, text="Звук", padding=5)
        sound_frame.pack(fill="x", pady=3)
        ttk.Label(sound_frame, text="Кол-во воспр.:").grid(row=0, column=0, padx=10, pady=3, sticky="e")
        self.num_plays_entry = ttk.Entry(sound_frame, width=8)
        self.num_plays_entry.insert(0, str(self.num_plays))
        self.num_plays_entry.grid(row=0, column=1, pady=3)
        self.num_plays_entry.bind("<FocusOut>", lambda e: self.update_num_plays())
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        ttk.Checkbutton(sound_frame, text="Воспроизводить сигнал", variable=self.sound_var, command=self.toggle_sound).grid(row=1, column=0, columnspan=3, pady=3, sticky="w")

        # Блок пресетов
        preset_frame = ttk.LabelFrame(main_frame, text="Пресеты", padding=5)
        preset_frame.pack(fill="x", pady=3)
        ttk.Label(preset_frame, text="Выбрать:").grid(row=0, column=0, padx=10, pady=3, sticky="e")
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, state="readonly", width=20)
        self.update_preset_menu()
        self.preset_combo.grid(row=0, column=1, pady=3)
        preset_button_frame = ttk.Frame(preset_frame)
        preset_button_frame.grid(row=0, column=2, padx=10, pady=3)
        ttk.Button(preset_button_frame, text="Сохранить", command=self.save_new_preset).pack(side="left", padx=5)
        ttk.Button(preset_button_frame, text="Удалить", command=self.delete_preset, style="danger.TButton").pack(side="left", padx=5)

        # Блок кнопок
        button_frame = ttk.Frame(main_frame, padding=5)
        button_frame.pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Старт", command=self.start_timer, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Стоп", command=self.stop_timer, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Сигнал", command=self.choose_signal, width=10).pack(side="left", padx=10)
        ttk.Button(button_frame, text="▶", command=self.play_sound, width=3).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Сброс поз.", command=self.reset_timer_position, width=10, style="danger.TButton").pack(side="left", padx=10)

        # Блок чекбоксов
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=3)
        self.clock_var = tk.BooleanVar(value=self.show_clock)
        ttk.Checkbutton(bottom_frame, text="Показывать время в покое", variable=self.clock_var, command=self.toggle_clock_mode).pack(side="left", pady=3)
        self.progress_var = tk.BooleanVar(value=self.show_progress)
        ttk.Checkbutton(bottom_frame, text="Показывать прогресс", variable=self.progress_var, command=self.toggle_progress_bar).pack(side="right", pady=3)

    def create_timer_window(self):
        """Создаёт прозрачное окно таймера с прогресс-баром."""
        self.timer_window = tk.Toplevel(self.root)
        self.timer_window.overrideredirect(True)
        self.timer_window.attributes("-topmost", True)
        self.timer_window.attributes("-alpha", self.opacity)

        if self.timer_pos:
            self.timer_window.geometry(f"300x80+{self.timer_pos['x']}+{self.timer_pos['y']}")
        else:
            screen_w = self.timer_window.winfo_screenwidth()
            screen_h = self.timer_window.winfo_screenheight()
            x = screen_w // 2 - 150
            y = screen_h // 2 - 40
            self.timer_window.geometry(f"300x80+{x}+{y}")

        self.timer_label = tk.Label(
            self.timer_window,
            text="00:00",
            font=(self.font_family, self.font_size, self.font_weight),
            fg=self.fg_positive,
            bg=self.bg_color,
        )
        self.timer_label.pack(expand=True, fill="both")

        self.progress_bar = ttk.Progressbar(
            self.timer_window,
            orient=tk.HORIZONTAL,
            length=300,
            mode="determinate",
            style="ThinProgressBar.TProgressbar"
        )
        if self.show_progress:
            self.progress_bar.pack(fill="x", padx=5, pady=2)

        self.timer_window.attributes("-transparentcolor", self.bg_color)

        self.timer_label.bind("<ButtonPress-1>", self.start_move)
        self.timer_label.bind("<B1-Motion>", self.do_move)
        self.timer_label.bind("<ButtonRelease-1>", lambda e: self.save_position())

    def toggle_clock_mode(self):
        """Включает/выключает показ текущего времени."""
        self.show_clock = self.clock_var.get()
        self.save_settings()
        self.update_clock()

    def toggle_progress_bar(self):
        """Включает/выключает прогресс-бар."""
        self.show_progress = self.progress_var.get()
        if self.show_progress:
            self.progress_bar.pack(fill="x", padx=5, pady=2)
        else:
            self.progress_bar.pack_forget()
        self.save_settings()

    def update_clock(self):
        """Обновляет часы в окне таймера, если он не активен."""
        if not self.running and self.time_left == 0:
            if self.show_clock:
                now = time.strftime("%H:%M:%S")
                self.timer_label.config(text=now, fg=self.fg_idle)
            else:
                self.timer_label.config(text="00:00", fg=self.fg_idle)
            if hasattr(self, "progress_bar") and self.show_progress:
                self.progress_bar["value"] = 0
                self.style.configure("ThinProgressBar.TProgressbar", background=self.fg_idle)
        self.root.after(1000, self.update_clock)

    def start_move(self, event):
        """Начинает перемещение окна таймера."""
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move(self, event):
        """Перемещает окно таймера."""
        x = self.timer_window.winfo_x() + (event.x - self._drag_x)
        y = self.timer_window.winfo_y() + (event.y - self._drag_y)
        self.timer_window.geometry(f"+{x}+{y}")

    def apply_settings(self):
        """Применяет настройки (шрифт, прозрачность, цвет фона, цвета текста)."""
        if not hasattr(self, "timer_window"):
            return
        self.font_size = int(self.font_scale.get())
        self.opacity = float(self.opacity_scale.get())
        self.bg_color = "white" if self.bg_var.get() == "Белый" else "black"
        self.timer_window.attributes("-alpha", self.opacity)
        self.timer_window.config(bg=self.bg_color)
        color = self.fg_positive if self.time_left > 0 else self.fg_negative if self.time_left < 0 else self.fg_idle
        self.timer_label.config(
            bg=self.bg_color,
            font=(self.font_family, self.font_size, self.font_weight),
            fg=color
        )
        if hasattr(self, "progress_bar"):
            self.style.configure("ThinProgressBar.TProgressbar", background=color)
        self.timer_window.attributes("-transparentcolor", self.bg_color)
        self.font_value_label.config(text=str(self.font_size))
        self.opacity_value_label.config(text=f"{self.opacity:.2f}")
        self.save_settings()

    def start_timer(self):
        """Запускает таймер."""
        try:
            minutes = int(self.minutes_entry.get())
            seconds = int(self.seconds_entry.get())
            self.time_left = minutes * 60 + seconds
            self.initial_time = self.time_left  # Сохраняем начальное время
            self.update_num_plays()
        except ValueError:
            return
        self.signal_played = False
        if not self.running:
            self.running = True
            threading.Thread(target=self.update_timer, daemon=True).start()

    def pause_timer(self):
        """Приостанавливает таймер."""
        self.running = False

    def stop_timer(self):
        """Останавливает таймер и сбрасывает время."""
        self.running = False
        self.time_left = 0
        self.initial_time = 0
        self.signal_played = False
        self.update_label()
        self.show_current_time()

    def show_current_time(self):
        """Показывает текущее время в окне таймера."""
        now = time.strftime("%H:%M:%S")
        self.timer_label.config(text=now, fg=self.fg_idle)
        if hasattr(self, "progress_bar") and self.show_progress:
            self.progress_bar["value"] = 0
            self.style.configure("ThinProgressBar.TProgressbar", background=self.fg_idle)

    def choose_signal(self):
        """Открывает диалог для выбора аудиофайла."""
        file_path = filedialog.askopenfilename(
            title="Выберите аудиофайл", filetypes=[("Аудио файлы", "*.wav *.mp3 *.ogg")]
        )
        if file_path:
            self.signal_file = file_path
            self.save_settings()

    def play_sound(self):
        """Воспроизводит выбранный звуковой файл."""
        if os.path.exists(self.signal_file):
            try:
                pygame.mixer.Sound(self.signal_file).play()
            except Exception as e:
                messagebox.showwarning("Ошибка", f"Не удалось воспроизвести: {e}")
        else:
            messagebox.showwarning("Ошибка", "Файл не найден!")

    def update_timer(self):
        """Обновляет таймер в отдельном потоке."""
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
        self.initial_time = 0
        self.root.after(0, self.update_clock)

    def update_label(self):
        """Потокобезопасное обновление метки таймера."""
        self.root.after(0, lambda: self._update_label_safe())

    def _update_label_safe(self):
        """Обновляет метку времени и прогресс-бар в окне таймера."""
        minutes, seconds = divmod(abs(self.time_left), 60)
        sign = "-" if self.time_left < 0 else ""
        color = self.fg_negative if self.time_left < 0 else self.fg_positive
        self.timer_label.config(text=f"{sign}{minutes:02d}:{seconds:02d}", fg=color)
        if hasattr(self, "progress_bar") and self.show_progress and self.initial_time > 0:
            progress = (self.time_left / self.initial_time) * 100 if self.time_left > 0 else 0
            self.progress_bar["value"] = progress
            self.style.configure("ThinProgressBar.TProgressbar", background=color)

    def update_num_plays(self):
        """Обновляет количество воспроизведений звука."""
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
        """Включает/выключает воспроизведение звука."""
        self.sound_enabled = self.sound_var.get()
        self.save_settings()

if __name__ == "__main__":
    """Запускает приложение и проверяет обновления."""
    root = ttk.Window(themename="flatly")
    icon_path = os.path.join(BASE_DIR, "clock.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    app = TransparentTimer(root)
    root.after(2000, lambda: threading.Thread(target=lambda: check_for_updates(root), daemon=True).start())
    root.mainloop()
    
    #pyinstaller --onefile --windowed --icon=clock.ico --add-data "alarm.wav;." --add-data "version.json;." timer.py