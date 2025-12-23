import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, colorchooser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter.font as tkfont
import time, os, sys, json, hashlib, requests, zipfile, io, subprocess, threading, shutil, tempfile
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
    """Проверяет наличие обновлений и запускает установщик."""
    GITHUB_REPO = "https://github.com/kostenkodm/countdown_timer"
    VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.json")
    RAW_VERSION_URL = f"{GITHUB_REPO}/raw/main/version.json"
    RELEASE_URL = f"{GITHUB_REPO}/releases/latest/download/TransparentTimerSetup.exe"

    # --- Версии ---
    def get_local_version():
        try:
            with open(VERSION_FILE, encoding="utf-8") as f:
                return json.load(f).get("version", "0.0.0")
        except Exception:
            return "0.0.0"

    def get_remote_version():
        try:
            r = requests.get(RAW_VERSION_URL, timeout=5)
            if r.status_code == 200:
                return r.json().get("version", "0.0.0")
        except Exception:
            pass
        return "0.0.0"

    def is_newer(v_remote, v_local):
        try:
            return tuple(map(int, v_remote.split("."))) > tuple(map(int, v_local.split(".")))
        except Exception:
            return False

    local = get_local_version()
    remote = get_remote_version()
    update_available = is_newer(remote, local)

    # --- GUI ---
    win = tk.Toplevel(parent)
    win.title("Обновление программы")
    win.geometry("340x200")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.grab_set()

    tk.Label(
        win,
        text=f"Текущая версия: {local}\nДоступная версия: {remote}",
        justify="center",
        font=("Segoe UI", 10)
    ).pack(pady=10)

    progress_var = tk.StringVar(value="Ожидание...")
    tk.Label(win, textvariable=progress_var, font=("Segoe UI", 9)).pack(pady=5)

    def download_and_install():
        try:
            temp_path = os.path.join(tempfile.gettempdir(), "TransparentTimerSetup.exe")
            progress_var.set("Скачивание установщика...")
            win.update()

            # Добавляем заголовки для отключения кэша и уникальный параметр
            headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
            import time
            timestamp = int(time.time())
            release_url_with_no_cache = f"{RELEASE_URL}?_={timestamp}"

            r = requests.get(release_url_with_no_cache, stream=True, timeout=30, headers=headers)
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(temp_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        progress = downloaded / total * 100
                        progress_var.set(f"Загрузка: {progress:.1f}%")
                        win.update()

            progress_var.set("Запуск установщика...")
            win.update()

            # Запускаем установщик и закрываем все окна
            subprocess.Popen([temp_path], shell=True)
            parent.destroy()  # Закрываем главное окно
            if hasattr(parent, "timer_window"):
                parent.timer_window.destroy()  # Закрываем окно таймера
            win.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить:\n{e}")
            win.destroy()

    def start_update():
        threading.Thread(target=download_and_install, daemon=True).start()

    action_text = "Обновить" if update_available else "Переустановить"
    tk.Button(win, text=action_text, width=20, command=start_update).pack(pady=10)
    tk.Button(win, text="Отмена", width=10, command=win.destroy).pack(pady=5)

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
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_reqheight()) // 2
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
        self.root.title(f"Таймер - {VERSION}")
        self.root.attributes("-topmost", True)
        self.settings_path = os.path.join(CONFIG_DIR, "settings.json")
        self.position_path = os.path.join(CONFIG_DIR, "position.json")
        self.show_clock = True
        self.show_progress = True
        self.hide_timer = False  # Новая переменная для скрытия таймера

        # Инициализация переменных
        self.time_left = 0
        self.initial_time = 0
        self.running = False
        self.signal_played = False
        self.signal_file = os.path.join(BASE_DIR, "alarm.wav")
        self.font_size = 33
        self.font_family = "Consolas"
        self.font_weight = "bold"
        self.bg_color = "white"
        self.opacity = 0.8
        self.fg_positive = "#00FF00"
        self.fg_negative = "#FF0000"
        self.fg_idle = "#808080"
        self.timer_pos = None
        self.num_plays = 1
        self.sound_enabled = True
        self.presets = {}
        self.theme_name = "flatly"

        # Скрываем нативный заголовок и создаём кастомный
        self.root.overrideredirect(True)
        self.create_custom_title_bar()

        # Настройка стиля
        self.style = ttk.Style()
        self.style.configure("Custom.TButton", background="#F0F0F0", foreground="#333333")
        self.style.configure("Custom.TButtonDark", background="#2F2F2F", foreground="#FFFFFF")

        # Загрузка настроек
        self.load_settings()
        try:
            self.root.style.theme_use(self.theme_name)
            self.update_title_bar_color()
        except Exception:
            self.theme_name = "flatly"
            self.root.style.theme_use(self.theme_name)
            self.update_title_bar_color()
        self.load_position()
        self.load_presets()
        self.create_main_window()
        self.create_timer_window()
        self.apply_settings()
        self.update_clock()

        # Привязка перемещения только к фрейму, исключая слайдеры и поля ввода
        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)
        self.root.bind("<ButtonRelease-1>", self.stop_move)

    def create_custom_title_bar(self):
        """Создаёт кастомную панель заголовка с кнопками меню."""
        self.title_bar = tk.Frame(self.root, bg="#F0F0F0", height=30)
        self.title_bar.pack(fill="x")

        # Кнопка "Кастомизация"
        self.customize_btn = ttk.Button(self.title_bar, text="Тема", style="secondary.TButton", command=self.open_theme_selection, width=5)
        self.customize_btn.pack(side="left", padx=5, pady=5)

        # Кнопка "Обновления"
        self.update_btn = ttk.Button(self.title_bar, text="Обновить", style="secondary.TButton", command=lambda: check_for_updates(self.root), width=5)
        self.update_btn.pack(side="left", padx=5, pady=5)

        # Кнопка "Справка"
        self.help_btn = ttk.Button(self.title_bar, text="?", style="secondary.TButton", command=self.show_info, width=2)
        self.help_btn.pack(side="left", padx=5, pady=5)

        # Метка с названием
        self.title_label = tk.Label(self.title_bar, text=f"Таймер - {VERSION}", bg="#F0F0F0", fg="#333333", font=("Segoe UI", 10))
        self.title_label.pack(side="left", padx=10, pady=5)

        # Кнопка закрытия
        self.close_button = tk.Button(self.title_bar, text="✕", command=self.root.quit, bg="#F0F0F0", fg="#FF0000", font=("Segoe UI", 10), bd=0, padx=5, pady=2)
        self.close_button.pack(side="right", padx=5)

    def start_move(self, event):
        """Начинает перемещение окна, если клик не на слайдере или поле ввода."""
        # Проверяем, не кликнули ли на слайдеры или поля ввода
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if widget not in [self.font_scale, self.opacity_scale, self.minutes_entry, self.seconds_entry, self.num_plays_entry]:
            self._drag_x = event.x
            self._drag_y = event.y

    def do_move(self, event):
        """Перемещает окно, если перемещение начато."""
        if hasattr(self, '_drag_x'):
            x = self.root.winfo_x() + (event.x - self._drag_x)
            y = self.root.winfo_y() + (event.y - self._drag_y)
            self.root.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        """Останавливает перемещение окна."""
        if hasattr(self, '_drag_x'):
            del self._drag_x
            del self._drag_y

    def update_title_bar_color(self):
        """Обновляет цвет кастомной панели заголовка в зависимости от темы."""
        if self.theme_name in ["darkly", "cyborg", "superhero", "vapor"]:
            color = "#2F2F2F"
            fg_color = "#FFFFFF"
            self.style.configure("Custom.TButton", background=color, foreground=fg_color)
            self.style.configure("Custom.TButtonDark", background=color, foreground=fg_color)
        else:
            color = "#F0F0F0"
            fg_color = "#333333"
            self.style.configure("Custom.TButton", background=color, foreground=fg_color)
            self.style.configure("Custom.TButtonDark", background=color, foreground="#FF0000")

        self.title_bar.config(bg=color)
        self.title_label.config(bg=color, fg=fg_color)
        self.close_button.config(bg=color, fg="#FF0000" if color == "#F0F0F0" else fg_color)

    def open_theme_selection(self):
        """Открывает модальное окно для выбора темы, шрифта и цветов."""
        theme_win = tk.Toplevel(self.root)
        theme_win.title("Настройки темы и шрифта")
        theme_win.geometry("300x360")
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
        
        # Цвет для времени > 0
        positive_frame = ttk.Frame(color_frame)
        positive_frame.pack(fill="x", pady=2)
        ttk.Button(positive_frame, text="Больше 0", command=lambda: self.choose_color("positive")).pack(side="left", fill="x", expand=True)
        ttk.Button(positive_frame, text="Сброс", command=lambda: self.reset_color("positive"), style="secondary.TButton", width=8).pack(side="right")
        
        # Цвет для времени < 0
        negative_frame = ttk.Frame(color_frame)
        negative_frame.pack(fill="x", pady=2)
        ttk.Button(negative_frame, text="Меньше 0", command=lambda: self.choose_color("negative")).pack(side="left", fill="x", expand=True)
        ttk.Button(negative_frame, text="Сброс", command=lambda: self.reset_color("negative"), style="secondary.TButton", width=8).pack(side="right")
        
        # Цвет для состояния покоя
        idle_frame = ttk.Frame(color_frame)
        idle_frame.pack(fill="x", pady=2)
        ttk.Button(idle_frame, text="Часы", command=lambda: self.choose_color("idle")).pack(side="left", fill="x", expand=True)
        ttk.Button(idle_frame, text="Сброс", command=lambda: self.reset_color("idle"), style="secondary.TButton", width=8).pack(side="right")

    def choose_color(self, color_type):
        """Открывает диалог выбора цвета для текста таймера."""
        initial_color = getattr(self, f"fg_{color_type}")
        color = colorchooser.askcolor(initialcolor=initial_color, title=f"Выберите цвет ({color_type})")
        if color[1]:
            if color_type == "positive":
                self.fg_positive = color[1]
            elif color_type == "negative":
                self.fg_negative = color[1]
            elif color_type == "idle":
                self.fg_idle = color[1]
            self.apply_settings()
            self.save_settings()

    def reset_color(self, color_type):
        """Сбрасывает цвет текста таймера к значению по умолчанию."""
        default_colors = {
            "positive": "#00FF00",
            "negative": "#FF0000",
            "idle": "#808080"
        }
        if color_type in default_colors:
            setattr(self, f"fg_{color_type}", default_colors[color_type])
            self.apply_settings()
            self.save_settings()

    def open_font_dialog(self):
        """Открывает диалог выбора шрифта."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Выбор шрифта")
        dialog.geometry("300x220")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.grab_set()

        ttk.Label(dialog, text="Семейство шрифта:").pack(pady=5)
        font_families = sorted(list(tkfont.families()))
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
        """Меняет тему на лету и сохраняет, обновляя цвет заголовка."""
        self.theme_name = new_theme
        try:
            self.root.style.theme_use(self.theme_name)
            if hasattr(self, "progress_bar"):
                color = self.fg_positive if self.time_left > 0 else self.fg_negative if self.time_left < 0 else self.fg_idle
                try:
                    self.style.configure("Horizontal.ThinProgressBar.TProgressbar", background=color)
                except Exception:
                    self.style.configure("Horizontal.TProgressbar", background=color)
            self.update_title_bar_color()
        except Exception:
            self.theme_name = "flatly"
            self.root.style.theme_use(self.theme_name)
            self.update_title_bar_color()
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
        # Основной фрейм (сдвигаем вниз из-за кастомного заголовка)
        main_frame = ttk.Frame(self.root, padding=8)
        main_frame.pack(fill="both", expand=True, pady=(0, 0))  # Отступ сверху для заголовка

        # Блок времени
        time_frame = ttk.Labelframe(main_frame, text="Время", padding=5)
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
        visual_frame = ttk.Labelframe(main_frame, text="Визуал", padding=5)
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
        sound_frame = ttk.Labelframe(main_frame, text="Звук", padding=5)
        sound_frame.pack(fill="x", pady=3)
        ttk.Label(sound_frame, text="Кол-во воспр.:").grid(row=0, column=0, padx=10, pady=3, sticky="e")
        self.num_plays_entry = ttk.Entry(sound_frame, width=8)
        self.num_plays_entry.insert(0, str(self.num_plays))
        self.num_plays_entry.grid(row=0, column=1, pady=3)
        self.num_plays_entry.bind("<FocusOut>", lambda e: self.update_num_plays())
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        ttk.Checkbutton(sound_frame, text="Воспроизводить сигнал", variable=self.sound_var, command=self.toggle_sound).grid(row=1, column=0, columnspan=3, pady=3, sticky="w")
        # Кнопки для выбора и воспроизведения сигнала справа
        ttk.Button(sound_frame, text="Выбрать", command=self.choose_signal, width=9, style="secondary.TButton").grid(row=0, column=2, padx=5, pady=3)
        ttk.Button(sound_frame, text="▶", command=self.play_sound, width=2, style="secondary.TButton").grid(row=0, column=3, padx=5, pady=3)

        # Блок пресетов
        preset_frame = ttk.Labelframe(main_frame, text="Пресеты", padding=5)
        preset_frame.pack(fill="x", pady=3)
        ttk.Label(preset_frame, text="Выбрать:").grid(row=0, column=0, padx=10, pady=3, sticky="e")
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, state="readonly", width=10)
        self.update_preset_menu()
        self.preset_combo.grid(row=0, column=1, pady=3)
        preset_button_frame = ttk.Frame(preset_frame)
        preset_button_frame.grid(row=0, column=2, padx=10, pady=3)
        ttk.Button(preset_button_frame, text="Сохранить", command=self.save_new_preset, style="secondary.TButton").pack(side="left", padx=3)
        ttk.Button(preset_button_frame, text="Удалить", command=self.delete_preset, style="secondary.TButton").pack(side="left", padx=3)

        # Блок кнопок
        button_frame = ttk.Frame(main_frame, padding=5)
        button_frame.pack(fill="x", pady=5)
        ttk.Button(button_frame, text="Старт", command=self.start_timer, width=13, style="success.TButton").pack(side="left", padx=3)
        ttk.Button(button_frame, text="Стоп", command=self.stop_timer, width=13).pack(side="left", padx=3)
        ttk.Button(button_frame, text="Сброс поз.", command=self.reset_timer_position, width=12, style="danger.TButton").pack(side="left", padx=3)

        # Блок чекбоксов
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="x", pady=3)
        self.clock_var = tk.BooleanVar(value=self.show_clock)
        ttk.Checkbutton(bottom_frame, text="Часы", variable=self.clock_var, command=self.toggle_clock_mode).pack(side="left", pady=3, padx=10)
        # Чекбокс для скрытия таймера
        self.hide_timer_var = tk.BooleanVar(value=self.hide_timer)
        ttk.Checkbutton(bottom_frame, text="Скрывать в покое", variable=self.hide_timer_var, command=self.toggle_timer_visibility).pack(side="left", pady=3, padx=10)
        self.progress_var = tk.BooleanVar(value=self.show_progress)
        ttk.Checkbutton(bottom_frame, text="Полоска", variable=self.progress_var, command=self.toggle_progress_bar).pack(side="left", pady=3, padx=10)


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

        try:
            self.progress_bar = ttk.Progressbar(
                self.timer_window,
                orient=tk.HORIZONTAL,
                length=300,
                mode="determinate",
                style="Horizontal.ThinProgressBar.TProgressbar"
            )
        except Exception:
            self.progress_bar = ttk.Progressbar(
                self.timer_window,
                orient=tk.HORIZONTAL,
                length=300,
                mode="determinate",
                style="Horizontal.TProgressbar"
            )
        if self.show_progress:
            self.progress_bar.pack(fill="x", padx=5, pady=2)

        self.timer_window.attributes("-transparentcolor", self.bg_color)

        self.timer_label.bind("<ButtonPress-1>", self.start_move_timer)
        self.timer_label.bind("<B1-Motion>", self.do_move_timer)
        self.timer_label.bind("<ButtonRelease-1>", lambda e: self.save_position())
        self.toggle_timer_visibility()  # Применяем начальное состояние видимости

    def start_move_timer(self, event):
        """Начинает перемещение окна таймера."""
        self._drag_x = event.x
        self._drag_y = event.y

    def do_move_timer(self, event):
        """Перемещает окно таймера."""
        x = self.timer_window.winfo_x() + (event.x - self._drag_x)
        y = self.timer_window.winfo_y() + (event.y - self._drag_y)
        self.timer_window.geometry(f"+{x}+{y}")

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

    def toggle_timer_visibility(self):
        """Включает/выключает видимость окна таймера."""
        self.hide_timer = self.hide_timer_var.get()
        if self.hide_timer and not self.running and self.time_left == 0:
            self.timer_window.withdraw()
        else:
            self.timer_window.deiconify()
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
                try:
                    self.style.configure("Horizontal.ThinProgressBar.TProgressbar", background=self.fg_idle)
                except Exception:
                    self.style.configure("Horizontal.TProgressbar", background=self.fg_idle)
            self.toggle_timer_visibility()
        self.root.after(1000, self.update_clock)

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
            try:
                self.style.configure("Horizontal.ThinProgressBar.TProgressbar", background=color)
            except Exception:
                self.style.configure("Horizontal.TProgressbar", background=color)
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
            self.initial_time = self.time_left
            self.update_num_plays()
        except ValueError:
            return
        self.signal_played = False
        if not self.running:
            self.running = True
            self.timer_window.deiconify()  # Показываем окно при старте
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
            try:
                self.style.configure("Horizontal.ThinProgressBar.TProgressbar", background=self.fg_idle)
            except Exception:
                self.style.configure("Horizontal.TProgressbar", background=self.fg_idle)

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
            try:
                self.style.configure("Horizontal.ThinProgressBar.TProgressbar", background=color)
            except Exception:
                self.style.configure("Horizontal.TProgressbar", background=color)

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
                    self.show_progress = data.get("show_progress", True)
                    self.num_plays = data.get("num_plays", 1)
                    self.sound_enabled = data.get("sound_enabled", True)
                    self.theme_name = data.get("theme_name", "flatly")
                    self.hide_timer = data.get("hide_timer", False)
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
            "hide_timer": self.hide_timer,
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
        x = screen_w // 2 - 150
        y = screen_h // 2 - 40
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
        }

    def apply_preset(self, event=None):
        """Применяет выбранный пресet."""
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

if __name__ == "__main__":
    """Запускает приложение."""
    root = ttk.Window(themename="flatly")
    icon_path = os.path.join(BASE_DIR, "clock.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    app = TransparentTimer(root)
    root.mainloop()

#pyinstaller --onefile --windowed --icon=clock.ico --add-data "alarm.wav;." --add-data "version.json;." timer.py