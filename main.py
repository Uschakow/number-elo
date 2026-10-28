# -*- coding: utf-8 -*-
"""
NUMBER — ELO
============
Игра-гадалка с рейтингом (ЭЛО), системой рангов и сохранением прогресса.

Исходная консольная версия переработана:
  * исправлены скрытые баги (см. список ниже);
  * устранено дублирование кода (5 почти одинаковых игровых циклов
    заменены единой конфигурацией режимов);
  * добавлен графический интерфейс на tkinter (только стандартная
    библиотека). Если tkinter не установлен — автоматически запускается
    консольная версия с теми же исправлениями.

Исправленные баги
-----------------
1. Повреждённый или некорректный save.json ронял игру при запуске
   (json.JSONDecodeError / KeyError). Теперь повреждённый файл переносится
   в save.json.bak, игра стартует с начальным прогрессом.
2. Запись сейва не была атомарной: сбой в момент записи ломал файл.
   Теперь сохранение выполняется через временный файл + os.replace().
3. В режимах «угадай число» не проверялся диапазон ввода: число 11 в
   режиме «0..10» засчитывалось как поражение, а мусорный ввод трактовался
   как проигрыш. Теперь ввод строго валидируется.
4. ЭЛО могло уйти в минус. Значение обрезается до 0.
5. У «Бота-стратега» ответ мог выходить за интервал [low; high], а в
   граничных случаях диапазоны random.randint оказывались пустыми.
   Ответ прижат к интервалу, смещения ограничены, добавлен запасной
   путь на случай, если бот «сдастся» (в оригинале — молчаливый выход).
6. Косметические баги консоли: «Система рангов» печаталась внутри цикла,
   дублирующий import random, мёртвые списки game_2/game_3/game_4,
   несогласованные названия («Роботблиц» / «Робоблиц»).
7. Результат бота-стратега мог никак не сообщаться игроку.

Запуск:
    python main.py         # GUI, если установлен tkinter
    python main.py --cli   # принудительно консольный режим
"""

import json
import os
import random
import sys
import tempfile

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # tkinter отсутствует в данной сборке Python
    tk = None
    messagebox = ttk = None


# ---------------------------------------------------------------------------
# Константы игры
# ---------------------------------------------------------------------------

SAVE_FILE = "save.json"
START_ELO = 1300
START_STATE = {"elo": START_ELO, "win": 0, "lose": 0}

# Режимы «игра против себя»: диапазон [lo; hi], награда/штраф за раунд.
MODES = {
    "easy": {"name": "Лёгкий", "lo": 1, "hi": 2, "win": (5, 15), "lose": (5, 15)},
    "medium": {"name": "Средний", "lo": 1, "hi": 3, "win": (20, 30), "lose": (20, 30)},
    "hard": {"name": "Сложный", "lo": 0, "hi": 10, "win": (75, 100), "lose": (10, 35)},
}

ROBO_RANGE = (1, 3)          # Робоблиц: диапазон загаданного числа
ROBO_WIN_DELTA = (20, 30)    # бот «промазал» — игрок выиграл раунд
ROBO_LOSE_DELTA = (20, 30)   # бот «угадал» — игрок проиграл раунд

QUIT_PENALTY = (45, 50)      # штраф за выход из незавершённой игры

# Таблица рангов: (минимальное ЭЛО, название). Отсортирована по возрастанию.
RANKS = [
    (0, "Бронза"),
    (700, "Железо"),
    (1300, "Серебро"),
    (1500, "Золото"),
    (1800, "Платина"),
    (2000, "Алмаз"),
    (2500, "Бриллиант"),
    (3000, "Легенда"),
]

BOT_TRAITS = ("Стандартный", "Агрессивный", "Недоумение")  # характеры бота
SMART_BOT_RANGE = (1, 100)  # диапазон «Бота-стратега»
SMART_FAST_ATTEMPTS = 6     # быстрее/равно — штраф, медленнее — награда


# ---------------------------------------------------------------------------
# Цвета и шрифты интерфейса
# ---------------------------------------------------------------------------

BG = "#151a23"
FG = "#e6e9ef"
SUB = "#98a2b3"
FIELD_BG = "#0e1116"
BUTTON_BG = "#2b3140"
BUTTON_ACTIVE = "#3b4356"
ACCENT = "#f6c344"
WIN_COLOR = "#5fd98a"
LOSE_COLOR = "#ff6b6b"
FONT = ("Segoe UI", 11)


# ---------------------------------------------------------------------------
# Ядро игры (не зависит от интерфейса)
# ---------------------------------------------------------------------------

def default_state():
    """Состояние нового игрока."""
    return dict(START_STATE)


def load_save():
    """Безопасная загрузка прогресса.

    Возвращает словарь {"elo", "win", "lose"}. Повреждённый файл
    переносится в save.json.bak, чтобы не терять данные безвозвратно.
    """
    if not os.path.exists(SAVE_FILE):
        return default_state()
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        state = {
            "elo": int(data.get("elo", 0)),
            "win": int(data.get("win", 0)),
            "lose": int(data.get("lose", 0)),
        }
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        try:
            if os.path.exists(SAVE_FILE):
                os.replace(SAVE_FILE, SAVE_FILE + ".bak")
        except OSError:
            pass
        return default_state()
    state["elo"] = max(0, state["elo"])
    return state


def save_game(elo, win, lose):
    """Атомарная запись прогресса (temp-файл + os.replace)."""
    data = {"elo": max(0, int(elo)), "win": int(win), "lose": int(lose)}
    fd, tmp = tempfile.mkstemp(dir=".", prefix=".save_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, SAVE_FILE)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def get_rank(elo):
    """Название ранга по количеству ЭЛО."""
    rank = RANKS[0][1]
    for threshold, name in RANKS:
        if elo >= threshold:
            rank = name
    return rank


def progress(elo):
    """Прогресс до следующего ранга.

    Возвращает кортеж (процент_0_100, имя_следующего_ранга_или_None,
    имя_текущего_ранга). Обрабатывает elo < 0 и максимальный ранг.
    """
    elo = max(0, elo)
    current_threshold = 0
    current_name = RANKS[0][1]
    next_threshold = None
    next_name = None
    for threshold, name in RANKS:
        if elo >= threshold:
            current_threshold, current_name = threshold, name
        else:
            next_threshold, next_name = threshold, name
            break
    if next_threshold is None:
        return 100.0, None, current_name
    span = next_threshold - current_threshold
    if span <= 0:
        return 100.0, next_name, current_name
    percent = (elo - current_threshold) / span * 100.0
    return max(0.0, min(100.0, percent)), next_name, current_name


def win_rate(win, lose):
    """Процент побед от общего числа сыгранных раундов."""
    total = win + lose
    return 0.0 if total == 0 else win / total * 100.0


class BotMind:
    """Модель мышления «Бота-стратега».

    Бинарный поиск с тремя характерами: «Стандартный» (иногда смещает
    ответ на 1..3 в сторону цели), «Агрессивный» (смещает сильнее) и
    «Недоумение» (тыкает в случайную точку внутри интервала).
    """

    def __init__(self, hint):
        self.hint = hint
        self.low, self.high = SMART_BOT_RANGE
        self.attempts = 0

    def step(self):
        """Один ход бота.

        Возвращает (число, найдено_ли). Если интервал исчерпан без
        результата — возвращает (None, False) как запасной путь.
        """
        if self.low > self.high:
            return None, False

        self.attempts += 1
        ideal = (self.low + self.high) // 2
        trait = random.choice(BOT_TRAITS)

        if trait == "Стандартный":
            if random.random() < 0.4 and self.hint != ideal:
                guess = ideal + random.randint(1, 3) \
                    if self.hint > ideal else ideal - random.randint(1, 3)
            else:
                guess = ideal
        elif trait == "Агрессивный":
            if self.hint > ideal:
                guess = ideal + random.randint(1, max(1, (self.high - ideal) // 2))
            elif self.hint < ideal:
                guess = ideal - random.randint(1, max(1, (ideal - self.low) // 2))
            else:
                guess = ideal
        else:  # «Недоумение» — случайная точка внутри интервала
            if self.high - self.low > 2:
                if random.choice((True, False)):
                    guess = random.randint(
                        self.low + 1,
                        min(self.high - 1, self.low + (self.high - self.low) // 3),
                    )
                else:
                    guess = random.randint(
                        max(self.low + 1, self.high - (self.high - self.low) // 3),
                        self.high - 1,
                    )
            else:
                guess = ideal

        guess = max(self.low, min(self.high, guess))

        if guess == self.hint:
            return guess, True
        if self.hint < guess:
            self.high = guess - 1
        else:
            self.low = guess + 1
        return guess, False

    def score(self):
        """Награда/штраф бота (в оригинале: быстрее 6 ходов — штраф)."""
        if self.attempts <= SMART_FAST_ATTEMPTS:
            return -(8 - self.attempts) * 15  # штраф игроку
        return self.attempts * 10             # награда игроку


# ---------------------------------------------------------------------------
# Графический интерфейс (tkinter). Доступен, если tkinter установлен.
# ---------------------------------------------------------------------------

if tk is not None:

    class BaseFrame(tk.Frame):
        """Общий предок всех экранов приложения."""

        def __init__(self, parent, app):
            super().__init__(parent, bg=BG)
            self.app = app

        def refresh_view(self):
            """Обновляет содержимое экрана при каждом его показе."""


    class MainMenu(BaseFrame):
        def __init__(self, parent, app):
            super().__init__(parent, app)

            tk.Label(self, text="NUMBER — ELO", font=("Segoe UI", 30, "bold"),
                     bg=BG, fg=ACCENT).pack(pady=(34, 0))
            tk.Label(self, text="Угадай число и подними свой рейтинг",
                     font=("Segoe UI", 13), bg=BG, fg=SUB).pack(pady=(0, 12))

            self.stat_label = tk.Label(self, font=("Segoe UI", 13, "bold"), bg=BG, fg=FG)
            self.stat_label.pack(pady=(0, 26))

            menu = tk.Frame(self, bg=BG)
            menu.pack()
            buttons = (
                ("Играть", "Accent.TButton", lambda: app.show_frame(ModeSelect)),
                ("Профиль", "TButton", lambda: app.show_frame(ProfileView)),
                ("Полка рангов", "TButton", lambda: app.show_frame(ShelfView)),
                ("Выход", "TButton", lambda: app.destroy()),
            )
            for text, style_name, cmd in buttons:
                ttk.Button(menu, text=text, command=cmd,
                           style=style_name, width=26).pack(pady=5)

        def refresh_view(self):
            self.stat_label.config(text=self.app.stat_line())


    class ModeSelect(BaseFrame):
        HINTS = {
            "easy": "Угадай число от 1 до 2.\nПобеда: +5..15 ЭЛО • Поражение: −5..15 ЭЛО",
            "medium": "Угадай число от 1 до 3.\nПобеда: +20..30 ЭЛО • Поражение: −20..30 ЭЛО",
            "hard": "Угадай число от 0 до 10.\nПобеда: +75..100 ЭЛО • Поражение: −10..35 ЭЛО",
            "robo": "Загадай число от 1 до 3 — Робоблиц попытается его угадать.",
            "smart": "Загадай число от 1 до 100, а Бот-стратег будет угадывать его по шагам.",
        }

        def __init__(self, parent, app):
            super().__init__(parent, app)

            tk.Label(self, text="Выбор режима", font=("Segoe UI", 22, "bold"),
                     bg=BG, fg=FG).pack(pady=(30, 16))

            self.mode_var = tk.StringVar(value="easy")
            box = tk.Frame(self, bg=BG)
            box.pack()
            options = (
                ("easy", "Лёгкий"),
                ("medium", "Средний"),
                ("hard", "Сложный"),
                ("robo", "Робоблиц"),
                ("smart", "Бот-стратег"),
            )
            for value, label in options:
                ttk.Radiobutton(box, text=label, value=value, variable=self.mode_var,
                                command=self._update_hint).pack(anchor="w", pady=3)

            self.hint_label = tk.Label(self, text="", font=("Segoe UI", 11),
                                       bg=BG, fg=SUB, justify="left")
            self.hint_label.pack(pady=(16, 10))

            ttk.Button(self, text="Начать игру", style="Accent.TButton", width=26,
                       command=self.start).pack(pady=4)
            ttk.Button(self, text="Назад", width=26,
                       command=lambda: app.show_frame(MainMenu)).pack(pady=4)
            self._update_hint()

        def _update_hint(self):
            self.hint_label.config(text=self.HINTS.get(self.mode_var.get(), ""))

        def start(self):
            key = self.mode_var.get()
            if key in MODES:
                self.app.launch_guess(key)
            elif key == "robo":
                self.app.show_frame(RoboBlitz)
            elif key == "smart":
                self.app.show_frame(SmartBot)


    class GuessGame(BaseFrame):
        """Режимы «Лёгкий / Средний / Сложный»: один раунд = одна попытка."""

        def __init__(self, parent, app):
            super().__init__(parent, app)
            self.mode_key = "easy"
            self.target = None
            self.finished = False

            self.mode_label = tk.Label(self, font=("Segoe UI", 22, "bold"), bg=BG, fg=FG)
            self.mode_label.pack(pady=(30, 4))
            self.prompt = tk.Label(self, font=("Segoe UI", 13), bg=BG, fg=SUB)
            self.prompt.pack(pady=(0, 16))

            row = tk.Frame(self, bg=BG)
            row.pack()
            self.entry = ttk.Entry(row, width=8, font=("Segoe UI", 18), justify="center")
            self.entry.pack(side="left", padx=(0, 10))
            self.check_btn = ttk.Button(row, text="Проверить", style="Accent.TButton",
                                        command=self.check)
            self.check_btn.pack(side="left")
            self.entry.bind("<Return>", lambda _e: self.check())

            self.result = tk.Label(self, font=("Segoe UI", 15, "bold"), bg=BG,
                                   fg=FG, wraplength=560)
            self.result.pack(pady=18)
            self.stats = tk.Label(self, font=("Segoe UI", 11), bg=BG, fg=SUB)
            self.stats.pack()

            bottom = tk.Frame(self, bg=BG)
            bottom.pack(side="bottom", pady=18)
            ttk.Button(bottom, text="Играть ещё", command=self.new_round).pack(side="left", padx=6)
            ttk.Button(bottom, text="В меню", command=self.quit_to_menu).pack(side="left", padx=6)

        def set_mode(self, mode_key):
            self.mode_key = mode_key

        def refresh_view(self):
            self.new_round()

        def new_round(self):
            cfg = MODES[self.mode_key]
            self.target = random.randint(cfg["lo"], cfg["hi"])
            self.finished = False
            self.mode_label.config(text=f"{cfg['name']} — угадай число!")
            self.prompt.config(
                text=f"Диапазон: от {cfg['lo']} до {cfg['hi']}. Одна попытка на раунд!")
            self.result.config(text="", fg=FG)
            self.stats.config(text=self.app.stat_line())
            self.entry.config(state="normal")
            self.check_btn.config(state="normal")
            self.entry.delete(0, "end")
            self.entry.focus_set()

        def check(self):
            if self.finished:
                return
            cfg = MODES[self.mode_key]
            raw = self.entry.get().strip()
            try:
                guess = int(raw)
            except ValueError:
                messagebox.showerror("Ошибка", "Введи число!")
                return
            if not (cfg["lo"] <= guess <= cfg["hi"]):
                messagebox.showerror("Ошибка",
                                     f"Число должно быть от {cfg['lo']} до {cfg['hi']}!")
                return

            self.finished = True
            self.entry.config(state="disabled")
            self.check_btn.config(state="disabled")

            if guess == self.target:
                delta = random.randint(*cfg["win"])
                self.app.apply_delta(delta, win=1)
                self.result.config(text=f"Победа! +{delta} ЭЛО", fg=WIN_COLOR)
            else:
                delta = random.randint(*cfg["lose"])
                self.app.apply_delta(-delta, lose=1)
                self.result.config(
                    text=f"Поражение! Было число {self.target}. −{delta} ЭЛО",
                    fg=LOSE_COLOR)
            self.stats.config(text=self.app.stat_line())

        def quit_to_menu(self):
            if not self.finished:
                if not messagebox.askyesno(
                        "Выход",
                        "Игра не завершена — штраф от 45 до 50 ЭЛО. Выйти?"):
                    return
                delta = random.randint(*QUIT_PENALTY)
                self.app.apply_delta(-delta)
                messagebox.showinfo("Штраф", f"Штраф за выход из игры: −{delta} ЭЛО")
            self.app.show_frame(ModeSelect)


    class RoboBlitz(BaseFrame):
        """Игрок загадывает число 1..3, робот пытается его угадать."""

        def __init__(self, parent, app):
            super().__init__(parent, app)
            self.finished = False

            tk.Label(self, text="Робоблиц", font=("Segoe UI", 22, "bold"),
                     bg=BG, fg=FG).pack(pady=(30, 4))
            tk.Label(self, text=f"Загадай число от {ROBO_RANGE[0]} до {ROBO_RANGE[1]} — "
                                "робот попытается его угадать!",
                     font=("Segoe UI", 13), bg=BG, fg=SUB).pack(pady=(0, 16))

            row = tk.Frame(self, bg=BG)
            row.pack()
            self.entry = ttk.Entry(row, width=8, font=("Segoe UI", 18), justify="center")
            self.entry.pack(side="left", padx=(0, 10))
            self.guess_btn = ttk.Button(row, text="Готово", style="Accent.TButton",
                                        command=self.guess)
            self.guess_btn.pack(side="left")
            self.entry.bind("<Return>", lambda _e: self.guess())

            self.result = tk.Label(self, font=("Segoe UI", 15, "bold"), bg=BG,
                                   fg=FG, wraplength=560)
            self.result.pack(pady=18)
            self.stats = tk.Label(self, font=("Segoe UI", 11), bg=BG, fg=SUB)
            self.stats.pack()

            bottom = tk.Frame(self, bg=BG)
            bottom.pack(side="bottom", pady=18)
            ttk.Button(bottom, text="Играть ещё", command=self.refresh_view).pack(side="left", padx=6)
            ttk.Button(bottom, text="В меню", command=self.quit_to_menu).pack(side="left", padx=6)

        def refresh_view(self):
            self.finished = False
            self.result.config(text="", fg=FG)
            self.stats.config(text=self.app.stat_line())
            self.entry.config(state="normal")
            self.guess_btn.config(state="normal")
            self.entry.delete(0, "end")
            self.entry.focus_set()

        def guess(self):
            if self.finished:
                return
            raw = self.entry.get().strip()
            try:
                choice = int(raw)
            except ValueError:
                messagebox.showerror("Ошибка", "Введи число!")
                return
            lo, hi = ROBO_RANGE
            if not (lo <= choice <= hi):
                messagebox.showerror("Ошибка", f"Число должно быть от {lo} до {hi}!")
                return

            self.finished = True
            self.entry.config(state="disabled")
            self.guess_btn.config(state="disabled")

            bot = random.randint(lo, hi)
            if choice == bot:
                delta = random.randint(*ROBO_LOSE_DELTA)
                self.app.apply_delta(-delta, lose=1)
                self.result.config(
                    text=f"Робот угадал твоё число {bot}! −{delta} ЭЛО", fg=LOSE_COLOR)
            else:
                delta = random.randint(*ROBO_WIN_DELTA)
                self.app.apply_delta(delta, win=1)
                self.result.config(
                    text=f"Робот промазал: его число {bot}. +{delta} ЭЛО", fg=WIN_COLOR)
            self.stats.config(text=self.app.stat_line())

        def quit_to_menu(self):
            if not self.finished:
                if not messagebox.askyesno(
                        "Выход",
                        "Игра не завершена — штраф от 45 до 50 ЭЛО. Выйти?"):
                    return
                delta = random.randint(*QUIT_PENALTY)
                self.app.apply_delta(-delta)
                messagebox.showinfo("Штраф", f"Штраф за выход из игры: −{delta} ЭЛО")
            self.app.show_frame(ModeSelect)


    class SmartBot(BaseFrame):
        """Бот-стратег угадывает число игрока (1..100) по шагам."""

        def __init__(self, parent, app):
            super().__init__(parent, app)
            self.hint = None
            self.mind = None
            self.phase = "setup"  # setup → playing → done

            tk.Label(self, text="Бот-стратег", font=("Segoe UI", 22, "bold"),
                     bg=BG, fg=FG).pack(pady=(26, 4))
            tk.Label(self, text=f"Загадай число от {SMART_BOT_RANGE[0]} до "
                                f"{SMART_BOT_RANGE[1]} — бот будет угадывать по шагам.",
                     font=("Segoe UI", 13), bg=BG, fg=SUB).pack(pady=(0, 12))

            setup_row = tk.Frame(self, bg=BG)
            setup_row.pack()
            self.entry = ttk.Entry(setup_row, width=8, font=("Segoe UI", 16), justify="center")
            self.entry.pack(side="left", padx=(0, 10))
            self.setup_btn = ttk.Button(setup_row, text="Загадать число",
                                        style="Accent.TButton", command=self.start_game)
            self.setup_btn.pack(side="left")
            self.entry.bind("<Return>", lambda _e: self.start_game())

            self.step_btn = ttk.Button(self, text="Ход бота →", command=self.step)
            self.step_btn.pack(pady=(12, 6))

            log_box = tk.Frame(self, bg=BG)
            log_box.pack(pady=6)
            self.log = tk.Text(log_box, height=9, width=52, bg=FIELD_BG, fg=FG,
                               font=("Segoe UI", 11), state="disabled", wrap="word",
                               relief="flat", padx=10, pady=10)
            scroll = ttk.Scrollbar(log_box, orient="vertical", command=self.log.yview)
            self.log.configure(yscrollcommand=scroll.set)
            self.log.pack(side="left")
            scroll.pack(side="left", fill="y")

            self.result = tk.Label(self, font=("Segoe UI", 15, "bold"), bg=BG,
                                   fg=FG, wraplength=580)
            self.result.pack(pady=(8, 2))
            self.stats = tk.Label(self, font=("Segoe UI", 11), bg=BG, fg=SUB)
            self.stats.pack()

            bottom = tk.Frame(self, bg=BG)
            bottom.pack(side="bottom", pady=10)
            ttk.Button(bottom, text="Играть ещё", command=self.refresh_view).pack(side="left", padx=6)
            ttk.Button(bottom, text="В меню", command=self.quit_to_menu).pack(side="left", padx=6)

        # -- утилиты журнала ------------------------------------------------
        def _log(self, msg):
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        def _log_clear(self):
            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.configure(state="disabled")

        # -- сценарий игры --------------------------------------------------
        def refresh_view(self):
            self.phase = "setup"
            self.hint = None
            self.mind = None
            self._log_clear()
            self.result.config(text="", fg=FG)
            self.stats.config(text=self.app.stat_line())
            self.entry.config(state="normal")
            self.setup_btn.config(state="normal")
            self.step_btn.config(state="disabled")
            self.entry.delete(0, "end")
            self.entry.focus_set()

        def start_game(self):
            raw = self.entry.get().strip()
            try:
                hint = int(raw)
            except ValueError:
                messagebox.showerror("Ошибка", "Введи число!")
                return
            lo, hi = SMART_BOT_RANGE
            if not (lo <= hint <= hi):
                messagebox.showerror("Ошибка", f"Число должно быть от {lo} до {hi}!")
                return

            self.hint = hint
            self.mind = BotMind(hint)
            self.phase = "playing"
            self._log(f"Загадано число {hint}. Бот думает...")
            self.entry.config(state="disabled")
            self.setup_btn.config(state="disabled")
            self.step_btn.config(state="normal")

        def step(self):
            if self.phase != "playing":
                return
            guess, found = self.mind.step()

            if guess is None:  # запасной путь: бот не нашёл число
                self.phase = "done"
                reward = self.mind.attempts * 10
                self.app.apply_delta(reward, win=1)
                self._log(f"Бот сдался после {self.mind.attempts} попыток и не нашёл число!")
                self.result.config(text=f"Бот не смог угадать. +{reward} ЭЛО", fg=WIN_COLOR)
                self._finish_round()
                return

            if found:
                self.phase = "done"
                score = self.mind.score()
                attempts = self.mind.attempts
                self._log(f"Бот угадал число {self.hint} за {attempts} ходов!")
                if score < 0:
                    self.app.apply_delta(score, lose=1)
                    self.result.config(
                        text=f"Бот расколол тебя за {attempts} ходов! {score} ЭЛО",
                        fg=LOSE_COLOR)
                else:
                    self.app.apply_delta(score, win=1)
                    self.result.config(
                        text=f"Бот мучился {attempts} ходов. Награда: +{score} ЭЛО",
                        fg=WIN_COLOR)
                self._finish_round()
                return

            self._log(f"Попытка {self.mind.attempts}: бот сказал «{guess}» — мимо.")

        def _finish_round(self):
            self.step_btn.config(state="disabled")
            self.stats.config(text=self.app.stat_line())

        def quit_to_menu(self):
            if self.phase == "playing":
                if not messagebox.askyesno(
                        "Выход",
                        "Бот ещё думает — штраф от 45 до 50 ЭЛО. Выйти?"):
                    return
                delta = random.randint(*QUIT_PENALTY)
                self.app.apply_delta(-delta)
                messagebox.showinfo("Штраф", f"Штраф за выход из игры: −{delta} ЭЛО")
            self.app.show_frame(ModeSelect)


    class ProfileView(BaseFrame):
        def __init__(self, parent, app):
            super().__init__(parent, app)

            tk.Label(self, text="Профиль", font=("Segoe UI", 22, "bold"), bg=BG,
                     fg=FG).pack(pady=(30, 12))

            self.rank_label = tk.Label(self, font=("Segoe UI", 20, "bold"), bg=BG, fg=ACCENT)
            self.rank_label.pack()
            self.elo_label = tk.Label(self, font=("Segoe UI", 14), bg=BG, fg=FG)
            self.elo_label.pack(pady=4)
            self.stats_label = tk.Label(self, font=("Segoe UI", 13), bg=BG, fg=FG)
            self.stats_label.pack()
            self.winrate_label = tk.Label(self, font=("Segoe UI", 13), bg=BG, fg=FG)
            self.winrate_label.pack()

            self.progress_target = tk.Label(self, font=("Segoe UI", 11), bg=BG, fg=SUB)
            self.progress_target.pack(pady=(24, 6))
            self.progress = ttk.Progressbar(self, maximum=100, length=420, mode="determinate")
            self.progress.pack()

            ttk.Button(self, text="Назад",
                       command=lambda: app.show_frame(MainMenu)).pack(pady=18)

        def refresh_view(self):
            d = self.app.data
            elo = max(0, d["elo"])
            rank = get_rank(elo)
            self.rank_label.config(text=rank)
            self.elo_label.config(text=f"ЭЛО: {elo}")
            self.stats_label.config(
                text=f"Победы: {d['win']}   •   Поражения: {d['lose']}")
            self.winrate_label.config(
                text=f"Средний показатель побед: {win_rate(d['win'], d['lose']):.1f}%")

            percent, next_name, _ = progress(elo)
            if next_name is None:
                self.progress_target.config(text="Максимальный ранг!")
                self.progress["value"] = 100
            else:
                self.progress_target.config(text=f"До ранга «{next_name}»: {percent:.1f}%")
                self.progress["value"] = percent


    class ShelfView(BaseFrame):
        def __init__(self, parent, app):
            super().__init__(parent, app)

            tk.Label(self, text="Полка рангов", font=("Segoe UI", 22, "bold"),
                     bg=BG, fg=FG).pack(pady=(24, 12))

            table = tk.Frame(self, bg=BG)
            table.pack()
            tk.Label(table, text="Ранг", font=("Segoe UI", 11, "bold"),
                     bg=BG, fg=ACCENT).grid(row=0, column=0, padx=44)
            tk.Label(table, text="Порог ЭЛО", font=("Segoe UI", 11, "bold"),
                     bg=BG, fg=ACCENT).grid(row=0, column=1, padx=44)
            for i, (threshold, name) in enumerate(RANKS, start=1):
                tk.Label(table, text=name, font=FONT, bg=BG, fg=FG).grid(row=i, column=0, pady=2)
                tk.Label(table, text=str(threshold), font=FONT, bg=BG, fg=SUB).grid(row=i, column=1, pady=2)

            tk.Label(self, text="Недавние обновления", font=("Segoe UI", 13, "bold"),
                     bg=BG, fg=FG).pack(pady=(16, 4))
            changes = (
                "12.10 — Добавлен новый режим: Робоблиц и Бот-Стратег!\n"
                "12.10 — Исправлены баги с вводом.\n"
                "14.10 — Удалено пиковое значение ЭЛО."
            )
            upd = tk.Text(self, height=5, width=46, bg=FIELD_BG, fg=FG,
                          font=("Segoe UI", 10), state="disabled", wrap="word", relief="flat")
            upd.pack()
            upd.configure(state="normal")
            upd.insert("1.0", changes)
            upd.configure(state="disabled")

            ttk.Button(self, text="Назад",
                       command=lambda: app.show_frame(MainMenu)).pack(pady=16)


    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("NUMBER — ELO")
            self.geometry("760x620")
            self.minsize(680, 540)
            self.configure(bg=BG)

            self.data = load_save()
            self._setup_style()

            container = tk.Frame(self, bg=BG)
            container.pack(fill="both", expand=True)
            container.grid_rowconfigure(0, weight=1)
            container.grid_columnconfigure(0, weight=1)

            self.frames = {}
            for frame_cls in (MainMenu, ModeSelect, GuessGame, RoboBlitz,
                              SmartBot, ProfileView, ShelfView):
                frame = frame_cls(container, self)
                self.frames[frame_cls] = frame
                frame.grid(row=0, column=0, sticky="nsew")

            self.show_frame(MainMenu)

        # -- состояние и сохранение ------------------------------------------
        def stat_line(self):
            d = self.data
            return (f"ЭЛО: {d['elo']}   •   Ранг: {get_rank(d['elo'])}   •   "
                    f"Победы: {d['win']}   •   Поражения: {d['lose']}")

        def apply_delta(self, elo_delta, win=0, lose=0):
            """Применяет изменение рейтинга/статистики и сохраняет прогресс."""
            d = self.data
            d["elo"] = max(0, d["elo"] + elo_delta)
            d["win"] += win
            d["lose"] += lose
            save_game(d["elo"], d["win"], d["lose"])

        # -- навигация --------------------------------------------------------
        def show_frame(self, frame_cls):
            frame = self.frames[frame_cls]
            frame.refresh_view()
            frame.tkraise()

        def launch_guess(self, mode_key):
            self.frames[GuessGame].set_mode(mode_key)
            self.show_frame(GuessGame)

        # -- оформление --------------------------------------------------------
        def _setup_style(self):
            style = ttk.Style(self)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            style.configure(".", background=BG, foreground=FG, font=FONT)
            style.configure("TButton", padding=8, background=BUTTON_BG,
                            foreground=FG, borderwidth=0)
            style.map("TButton",
                      background=[("active", BUTTON_ACTIVE), ("pressed", BUTTON_ACTIVE)])
            style.configure("Accent.TButton", background=ACCENT, foreground="#14161b",
                            font=("Segoe UI", 11, "bold"), padding=8, borderwidth=0)
            style.map("Accent.TButton",
                      background=[("active", "#f7cf5f"), ("pressed", "#e0b33c")])
            style.configure("TEntry", fieldbackground=FIELD_BG, foreground=FG,
                            insertcolor=FG, padding=6)
            style.configure("TRadiobutton", background=BG, foreground=FG,
                            font=FONT, padding=3)
            style.configure("TProgressbar", troughcolor=FIELD_BG, background=ACCENT)
            style.configure("TScrollbar", background=BUTTON_BG, troughcolor=FIELD_BG)


# ---------------------------------------------------------------------------
# Консольный режим (если tkinter не установлен или запрошен через --cli)
# ---------------------------------------------------------------------------

def _console_confirm_quit(data):
    """Подтверждение выхода из незавершённой игры со штрафом.

    Возвращает True, если игрок подтвердил выход.
    """
    ans = input("Ты уверен? Незавершённая игра — минус рейтинг (y/n): ").strip().lower()
    if ans == "y":
        delta = random.randint(*QUIT_PENALTY)
        data["elo"] = max(0, data["elo"] - delta)
        save_game(data["elo"], data["win"], data["lose"])
        print(f"Штраф за незавершённый выход: −{delta} ЭЛО. Итог: {data['elo']}")
        return True
    if ans != "n":
        print("Неправильный ввод")
    return False


def _console_guess(mode_key, data):
    """Один из режимов «угадай число» в консоли."""
    cfg = MODES[mode_key]
    while True:
        target = random.randint(cfg["lo"], cfg["hi"])
        print(f"{cfg['name']}: угадай число от {cfg['lo']} до {cfg['hi']}! "
              f"(рейтинг: {data['elo']})")
        raw = input("Ход (Q — выйти) > ").strip()
        if raw.lower() == "q":
            if _console_confirm_quit(data):
                return
            continue
        try:
            guess = int(raw)
        except ValueError:
            print("Введи число!")
            continue
        if not (cfg["lo"] <= guess <= cfg["hi"]):
            print(f"Число должно быть от {cfg['lo']} до {cfg['hi']}!")
            continue
        if guess == target:
            delta = random.randint(*cfg["win"])
            data["elo"] += delta
            data["win"] += 1
            print(f"Победа! +{delta} ЭЛО (итого: {data['elo']})")
        else:
            delta = random.randint(*cfg["lose"])
            data["elo"] = max(0, data["elo"] - delta)
            data["lose"] += 1
            print(f"Поражение! Было число {target}. −{delta} ЭЛО (итого: {data['elo']})")
        save_game(data["elo"], data["win"], data["lose"])
        if input("Играть ещё? (y/n): ").strip().lower() != "y":
            return


def _console_robo(data):
    """Робоблиц: игрок загадывает число, робот пытается угадать."""
    lo, hi = ROBO_RANGE
    while True:
        print(f"Загадай число от {lo} до {hi} — Робоблиц попытается угадать! "
              f"(рейтинг: {data['elo']})")
        raw = input("Ввод (Q — выйти) > ").strip()
        if raw.lower() == "q":
            if _console_confirm_quit(data):
                return
            continue
        try:
            choice = int(raw)
        except ValueError:
            print("Это не число.")
            continue
        if not (lo <= choice <= hi):
            print("Число должно быть от 1 до 3!")
            continue

        bot = random.randint(lo, hi)
        if choice == bot:
            delta = random.randint(*ROBO_LOSE_DELTA)
            data["elo"] = max(0, data["elo"] - delta)
            data["lose"] += 1
            print(f"Робот угадал твоё число {bot}! −{delta} ЭЛО (итого: {data['elo']})")
        else:
            delta = random.randint(*ROBO_WIN_DELTA)
            data["elo"] += delta
            data["win"] += 1
            print(f"Робот промазал: его число {bot}. +{delta} ЭЛО (итого: {data['elo']})")
        save_game(data["elo"], data["win"], data["lose"])
        if input("Играть ещё? (y/n): ").strip().lower() != "y":
            return


def _console_smart(data):
    """Бот-стратег угадывает число игрока по шагам."""
    lo, hi = SMART_BOT_RANGE
    while True:
        print(f"Загадай число от {lo} до {hi} — бот-стратег будет угадывать "
              f"(рейтинг: {data['elo']})")
        while True:
            raw = input("Число (Q — выйти) > ").strip()
            if raw.lower() == "q":
                if _console_confirm_quit(data):
                    return
                continue
            try:
                hint = int(raw)
            except ValueError:
                print("Введи число!")
                continue
            if lo <= hint <= hi:
                break
            print(f"Число должно быть от {lo} до {hi}!")

        mind = BotMind(hint)
        while True:
            guess, found = mind.step()
            if guess is None:  # запасной путь: бот не нашёл число
                reward = mind.attempts * 10
                data["elo"] += reward
                data["win"] += 1
                save_game(data["elo"], data["win"], data["lose"])
                print(f"Бот сдался и не нашёл число! +{reward} ЭЛО (итого: {data['elo']})")
                break
            print(f"Ход {mind.attempts}: бот сказал «{guess}»")
            if found:
                score = mind.score()
                if score < 0:
                    data["elo"] = max(0, data["elo"] + score)
                    data["lose"] += 1
                    print(f"Бот угадал число за {mind.attempts} ходов! "
                          f"Штраф: {score} ЭЛО (итого: {data['elo']})")
                else:
                    data["elo"] += score
                    data["win"] += 1
                    print(f"Бот мучился {mind.attempts} ходов. "
                          f"Награда: +{score} ЭЛО (итого: {data['elo']})")
                save_game(data["elo"], data["win"], data["lose"])
                break
        if input("Играть ещё? (y/n): ").strip().lower() != "y":
            return


def _console_profile(data):
    elo = max(0, data["elo"])
    percent, next_name, _ = progress(elo)
    print("=" * 60)
    print(f"ЭЛО: {elo} | Ранг: {get_rank(elo)}")
    print(f"Победы: {data['win']} | Поражения: {data['lose']} | "
          f"Винрейт: {win_rate(data['win'], data['lose']):.1f}%")
    if next_name is None:
        print("Максимальный ранг!")
    else:
        print(f"До ранга «{next_name}»: {percent:.1f}%")
    print("=" * 60)


# Клавиши выбора режимов в консоли: короткая клавиша -> ключ конфигурации.
CONSOLE_MODE_KEYS = {"e": "easy", "n": "medium", "h": "hard",
                     "b": "robo", "s": "smart"}


def _console_mode(data):
    while True:
        print("Игра против себя: Лёгкий — e | Средний — n | Сложный — h")
        print("Игра против ботов: Робоблиц — b | Бот-стратег — s | Назад — q")
        key = input("> ").strip().lower()
        if key == "q":
            return
        mode = CONSOLE_MODE_KEYS.get(key)
        if mode is None:
            print("Неправильный ввод")
            continue
        if mode in MODES:
            _console_guess(mode, data)
            return
        if mode == "robo":
            _console_robo(data)
            return
        if mode == "smart":
            _console_smart(data)
            return


def _console_main():
    data = load_save()
    while True:
        print()
        print("=" * 26, "NUMBER—ELO", "=" * 26)
        print(f"Рейтинг: {data['elo']} | Ранг: {get_rank(data['elo'])}")
        print("Играть — G | Профиль — P | Полка рангов — S | Выход — Q")
        cho = input("> ").strip().lower()
        if cho == "q":
            print("Выходим...")
            return
        if cho == "p":
            _console_profile(data)
        elif cho == "s":
            for threshold, name in RANKS:
                print(f"{name} — от {threshold} ЭЛО")
        elif cho == "g":
            _console_mode(data)
        else:
            print("Неправильный ввод")


def main():
    if "--cli" not in sys.argv and tk is not None:
        App().mainloop()
        return
    if tk is None:
        print("tkinter не установлен — запускаю консольную версию.")
        print("Для графического интерфейса установите python3-tk, "
              "например: sudo apt install python3-tk")
    try:
        _console_main()
    except (EOFError, KeyboardInterrupt):
        print("\nВыходим...")


if __name__ == "__main__":
    main()
