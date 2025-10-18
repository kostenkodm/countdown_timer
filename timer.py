import tkinter as tk
from tkinter import filedialog
import time
import threading
import winsound
import os
import sys
import json

# === Безопасные пути для exe ===
def get_base_dir():
    if hasattr(sys, '_MEIPASS'):  # если exe
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def get_config_dir():
    path = os.path.join(os.getenv("APPDATA"), "TransparentTimer")
    os.makedirs(path, exist_ok=True)
    return path

BASE_DIR = get_base_dir()
CONFIG_DIR = get_config_dir()


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

        # Загружаем настройки
        self.load_settings()
        self.load_position()

        # Создаём интерфейс
        self.create_main_window()
        self.create_timer_window()
        self.apply_settings()

    # === Настройки ===
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
            "opacity": self.opacity
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
            geom = self.timer_window.geometry()
            x = self.timer_window.winfo_x()
            y = self.timer_window.winfo_y()
            data = {"x": x, "y": y}
            with open(self.position_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    # === Главное окно ===
    def create_main_window(self):
        frame = tk.Frame(self.root)
        self.root.attributes("-topmost", True)
        frame.pack(padx=10, pady=10)

        # Минуты и секунды
        tk.Label(frame, text="Минуты:").grid(row=0, column=0, padx=5)
        self.minutes_entry = tk.Entry(frame, width=4)
        self.minutes_entry.insert(0, "1")
        self.minutes_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="Секунды:").grid(row=0, column=2, padx=5)
        self.seconds_entry = tk.Entry(frame, width=4)
        self.seconds_entry.insert(0, "0")
        self.seconds_entry.grid(row=0, column=3, padx=5)

        # Высота шрифта
        tk.Label(frame, text="Высота шрифта:").grid(row=1, column=0, padx=5)
        self.font_scale = tk.Scale(frame, from_=10, to=60, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings())
        self.font_scale.set(self.font_size)
        self.font_scale.grid(row=1, column=1, columnspan=3, sticky="we", padx=5)

        # Прозрачность окна
        tk.Label(frame, text="Прозрачность окна:").grid(row=2, column=0, padx=5)
        self.opacity_scale = tk.Scale(frame, from_=0.1, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, command=lambda v: self.apply_settings())
        self.opacity_scale.set(self.opacity)
        self.opacity_scale.grid(row=2, column=1, columnspan=3, sticky="we", padx=5)

        # Цвет фона
        tk.Label(frame, text="Цвет фона:").grid(row=3, column=0, padx=5)
        self.bg_var = tk.StringVar(value="Белый" if self.bg_color == "white" else "Чёрный")
        bg_menu = tk.OptionMenu(frame, self.bg_var, "Белый", "Чёрный", command=lambda v: self.apply_settings())
        bg_menu.grid(row=3, column=1, columnspan=3, sticky="we", padx=5, pady=5)

        # Кнопки
        tk.Button(frame, text="Старт", command=self.start_timer).grid(row=4, column=0, padx=5, pady=5)
        tk.Button(frame, text="Пауза", command=self.pause_timer).grid(row=4, column=1, padx=5, pady=5)
        tk.Button(frame, text="Стоп", command=self.stop_timer).grid(row=4, column=2, padx=5, pady=5)
        tk.Button(frame, text="Сигнал", command=self.choose_signal).grid(row=4, column=3, padx=5, pady=5)

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
            bg=self.bg_color
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

    # === Применение настроек ===
    def apply_settings(self):
        self.font_size = self.font_scale.get()
        self.opacity = self.opacity_scale.get()
        self.bg_color = "white" if self.bg_var.get() == "Белый" else "black"

        self.timer_window.attributes("-alpha", self.opacity)
        self.timer_window.config(bg=self.bg_color)
        self.timer_label.config(bg=self.bg_color, font=("Consolas", self.font_size, "bold"))
        bg_choice = self.bg_var.get()
        if bg_choice == "Чёрный":
            self.bg_color = "black"
        elif bg_choice == "Белый":
            self.bg_color = "white"
        else:
            self.bg_color = "white"  # на случай ошибки

        self.timer_label.config(bg=self.bg_color)
        self.timer_window.config(bg=self.bg_color)
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
        file_path = filedialog.askopenfilename(title="Выберите WAV-файл", filetypes=[("WAV файлы", "*.wav")])
        if file_path:
            self.signal_file = file_path
            self.save_settings()

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
    else:
        root.iconbitmap(default="")

    app = TransparentTimer(root)
    root.mainloop()
