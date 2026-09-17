# ============================================================
#  ДЕТЕКТОР «Я ЗАЛИПАЮ» — Kivy APK v3.0
#  Работает в фоне, вибрация, уведомления
# ============================================================
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.utils import get_color_from_hex, platform

import json
import os
import time
from datetime import datetime

# --- Платформенные импорты ---
IS_ANDROID = (platform == "android")

if IS_ANDROID:
    try:
        from android.permissions import request_permissions, Permission
        request_permissions([
            Permission.VIBRATE,
            Permission.POST_NOTIFICATIONS,
            Permission.WAKE_LOCK,
            Permission.FOREGROUND_SERVICE,
        ])
    except Exception as e:
        print("Permissions error:", e)

try:
    from plyer import vibrator
    HAS_VIBRATOR = True
except Exception:
    HAS_VIBRATOR = False

try:
    from plyer import notification
    HAS_NOTIF = True
except Exception:
    HAS_NOTIF = False


VERSION = "3.0"
DATA_FILE = os.path.join(os.path.expanduser("~"), "zalip_log.json")
DEFAULT_INTERVAL_MIN = 30

CATEGORIES = [
    ("work",   "Работа / Учёба",       "#4CAF50", "💼"),
    ("rest",   "Отдых",                "#2196F3", "☕"),
    ("social", "Соцсети / Мессенджеры","#FF9800", "📱"),
    ("games",  "Игры",                 "#9C27B0", "🎮"),
    ("stuck",  "Залипаю",              "#F44336", "🌀"),
    ("other",  "Другое",               "#607D8B", "❓"),
]
CAT_BY_ID = {c[0]: c for c in CATEGORIES}

BG_COLOR     = get_color_from_hex("#1a1a24")
PANEL_COLOR  = get_color_from_hex("#252536")
TEXT_COLOR   = get_color_from_hex("#ffffff")
DIM_COLOR    = get_color_from_hex("#8888a0")
ACCENT_COLOR = get_color_from_hex("#80c8ff")


# ============================================================
#  ДАННЫЕ
# ============================================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"records": [], "interval_min": DEFAULT_INTERVAL_MIN,
            "last_ask_time": time.time()}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save error:", e)


# ============================================================
#  СИГНАЛ
# ============================================================
def signal_attention():
    if HAS_VIBRATOR:
        try:
            vibrator.vibrate(0.4)
            Clock.schedule_once(lambda dt: _vibro_again(), 0.3)
        except Exception as e:
            print("vibro err:", e)

    if HAS_NOTIF:
        try:
            notification.notify(
                title="🕐 Что ты делаешь?",
                message="Открой детектор и ответь",
                timeout=15,
            )
        except Exception as e:
            print("notif err:", e)


def _vibro_again():
    if HAS_VIBRATOR:
        try:
            vibrator.vibrate(0.4)
        except Exception:
            pass


# ============================================================
#  ПОПАП ВОПРОСА
# ============================================================
class AskPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.title = ""
        self.title_size = 1
        self.separator_height = 0
        self.background_color = (0, 0, 0, 0.7)
        self.background = ""
        self.size_hint = (0.95, 0.92)
        self.auto_dismiss = False

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6))
        with root.canvas.before:
            Color(*PANEL_COLOR)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size,
                                        radius=[dp(15)])
        root.bind(pos=self._update_bg, size=self._update_bg)

        now_str = datetime.now().strftime("%H:%M")

        root.add_widget(Label(
            text="🕐 Что ты делаешь\nпрямо сейчас?",
            font_size=dp(20), bold=True, color=TEXT_COLOR,
            size_hint_y=None, height=dp(70),
            halign="center", valign="middle",
        ))

        root.add_widget(Label(
            text=now_str, font_size=dp(14), color=DIM_COLOR,
            size_hint_y=None, height=dp(22),
        ))

        for cat_id, cat_name, cat_color, emoji in CATEGORIES:
            btn = Button(
                text=f"{emoji}  {cat_name}",
                font_size=dp(15), bold=True,
                background_normal="",
                background_color=get_color_from_hex(cat_color),
                size_hint_y=None, height=dp(46),
            )
            btn.bind(on_press=lambda b, c=cat_id: self.select(c))
            root.add_widget(btn)

        root.add_widget(Label(
            text="Комментарий (необязательно):",
            font_size=dp(11), color=DIM_COLOR,
            size_hint_y=None, height=dp(18),
        ))

        self.comment_input = TextInput(
            multiline=False, font_size=dp(13),
            background_color=get_color_from_hex("#32324a"),
            foreground_color=TEXT_COLOR,
            cursor_color=ACCENT_COLOR,
            size_hint_y=None, height=dp(40),
        )
        root.add_widget(self.comment_input)

        skip_btn = Button(
            text="Пропустить", font_size=dp(13),
            background_normal="",
            background_color=get_color_from_hex("#444460"),
            size_hint_y=None, height=dp(38),
        )
        skip_btn.bind(on_press=self.skip)
        root.add_widget(skip_btn)

        self.content = root

    def _update_bg(self, instance, value):
        self._bg.pos = instance.pos
        self._bg.size = instance.size

    def select(self, cat_id):
        comment = self.comment_input.text.strip()
        now = datetime.now()
        rec = {
            "time": now.strftime("%Y-%m-%d %H:%M"),
            "timestamp": now.timestamp(),
            "category": cat_id,
            "comment": comment,
        }
        self.app.data["records"].append(rec)
        save_data(self.app.data)
        self.app.refresh_recent()
        self.app.status_label.text = f"✓ {CAT_BY_ID[cat_id][1]}"
        self.app.status_label.color = get_color_from_hex(CAT_BY_ID[cat_id][2])
        self.app.ask_popup = None
        self.dismiss()
        self.app.reset_timer()

    def skip(self):
        self.app.status_label.text = "Пропущено"
        self.app.status_label.color = DIM_COLOR
        self.app.ask_popup = None
        self.dismiss()
        self.app.reset_timer()


# ============================================================
#  ПОПАП СТАТИСТИКИ
# ============================================================
class StatsPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.title = ""
        self.title_size = 1
        self.separator_height = 0
        self.background_color = (0, 0, 0, 0.7)
        self.background = ""
        self.size_hint = (0.95, 0.92)

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(6))
        with root.canvas.before:
            Color(*PANEL_COLOR)
            self._bg = RoundedRectangle(pos=root.pos, size=root.size,
                                        radius=[dp(15)])
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Label(
            text="📊 Статистика", font_size=dp(20), bold=True,
            color=TEXT_COLOR, size_hint_y=None, height=dp(36),
        ))

        records = app.data["records"]

        if not records:
            root.add_widget(Label(
                text="Пока нет данных", font_size=dp(15),
                color=DIM_COLOR,
            ))
        else:
            counts = {}
            for rec in records:
                cat = rec.get("category", "other")
                counts[cat] = counts.get(cat, 0) + 1
            total = sum(counts.values())

            root.add_widget(Label(
                text=f"Всего записей: {total}",
                font_size=dp(13), color=ACCENT_COLOR,
                size_hint_y=None, height=dp(24),
            ))

            scroll = ScrollView()
            inner = BoxLayout(orientation="vertical",
                              size_hint_y=None, spacing=dp(8))
            inner.bind(minimum_height=inner.setter("height"))

            sorted_cats = sorted(counts.items(), key=lambda x: -x[1])
            for cat, cnt in sorted_cats:
                pct = cnt * 100 / total
                info = CAT_BY_ID.get(cat, ("other", "?", "#607D8B", "?"))
                color = get_color_from_hex(info[2])

                row = BoxLayout(orientation="vertical",
                                size_hint_y=None, height=dp(48))
                top = BoxLayout(size_hint_y=None, height=dp(22))
                top.add_widget(Label(
                    text=f"{info[3]}  {info[1]}",
                    font_size=dp(12), color=TEXT_COLOR,
                    halign="left",
                ))
                top.add_widget(Label(
                    text=f"{pct:.0f}%  ({cnt})",
                    font_size=dp(11), color=DIM_COLOR,
                    halign="right", size_hint_x=0.4,
                ))
                row.add_widget(top)

                bar_container = FloatLayout(size_hint_y=None, height=dp(10))
                bar_bg = BoxLayout()
                with bar_bg.canvas.before:
                    Color(*get_color_from_hex("#32324a"))
                    rect1 = Rectangle(pos=bar_bg.pos, size=bar_bg.size)
                bar_bg.bind(
                    pos=lambda i, v, r=rect1: setattr(r, "pos", v),
                    size=lambda i, v, r=rect1: setattr(r, "size", v),
                )

                bar = BoxLayout(size_hint_x=max(0.01, pct / 100))
                with bar.canvas.before:
                    Color(*color)
                    rect2 = Rectangle(pos=bar.pos, size=bar.size)
                bar.bind(
                    pos=lambda i, v, r=rect2: setattr(r, "pos", v),
                    size=lambda i, v, r=rect2: setattr(r, "size", v),
                )
                bar_container.add_widget(bar_bg)
                bar_container.add_widget(bar)
                row.add_widget(bar_container)
                inner.add_widget(row)

            scroll.add_widget(inner)
            root.add_widget(scroll)

        btn_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        exp_btn = Button(
            text="📄 CSV", font_size=dp(13), bold=True,
            background_normal="",
            background_color=get_color_from_hex("#4CAF50"),
        )
        exp_btn.bind(on_press=lambda b: self.app.export_csv())
        btn_row.add_widget(exp_btn)

        clear_btn = Button(
            text="🗑 Очистить", font_size=dp(13), bold=True,
            background_normal="",
            background_color=get_color_from_hex("#F44336"),
        )
        clear_btn.bind(on_press=lambda b: self.app.clear_all(self))
        btn_row.add_widget(clear_btn)

        close_btn = Button(
            text="Закрыть", font_size=dp(13), bold=True,
            background_normal="",
            background_color=get_color_from_hex("#444460"),
        )
        close_btn.bind(on_press=lambda b: self.dismiss())
        btn_row.add_widget(close_btn)
        root.add_widget(btn_row)
        self.content = root

    def _update_bg(self, instance, value):
        self._bg.pos = instance.pos
        self._bg.size = instance.size


# ============================================================
#  ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================
class ZalipApp(App):
    def build(self):
        self.title = f"Детектор «Я залипаю» v{VERSION}"
        self.data = load_data()
        self.interval_sec = self.data.get("interval_min", DEFAULT_INTERVAL_MIN) * 60
        self.last_ask_time = self.data.get("last_ask_time", time.time())

        # Если прошло больше интервала — сразу спрашиваем
        if time.time() - self.last_ask_time >= self.interval_sec:
            Clock.schedule_once(lambda dt: self.ask_now(), 1.5)

        self.ask_popup = None
        self.paused = False

        root = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        with root.canvas.before:
            Color(*BG_COLOR)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        root.add_widget(Label(
            text="🧠 Детектор «Я залипаю»",
            font_size=dp(22), bold=True, color=TEXT_COLOR,
            size_hint_y=None, height=dp(40),
        ))
        root.add_widget(Label(
            text="Зеркало для твоего времени",
            font_size=dp(12), color=DIM_COLOR,
            size_hint_y=None, height=dp(20),
        ))

        self.status_label = Label(
            text="Работает", font_size=dp(13),
            color=get_color_from_hex("#4CAF50"),
            size_hint_y=None, height=dp(26),
        )
        root.add_widget(self.status_label)

        self.timer_label = Label(
            text="--:--", font_size=dp(44), bold=True,
            color=ACCENT_COLOR, size_hint_y=None, height=dp(70),
        )
        root.add_widget(self.timer_label)

        root.add_widget(Label(
            text="до следующего вопроса",
            font_size=dp(11), color=DIM_COLOR,
            size_hint_y=None, height=dp(18),
        ))

        btn_box = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(6))
        stat_btn = Button(
            text="📊", font_size=dp(16), bold=True,
            background_normal="",
            background_color=get_color_from_hex("#2196F3"),
            size_hint_x=0.3,
        )
        stat_btn.bind(on_press=lambda b: self.show_stats())
        btn_box.add_widget(stat_btn)

        ask_btn = Button(
            text="❓ Спросить", font_size=dp(13), bold=True,
            background_normal="",
            background_color=get_color_from_hex("#FF9800"),
        )
        ask_btn.bind(on_press=lambda b: self.force_ask())
        btn_box.add_widget(ask_btn)

        self.pause_btn = Button(
            text="⏸", font_size=dp(16), bold=True,
            background_normal="",
            background_color=get_color_from_hex("#9C27B0"),
            size_hint_x=0.3,
        )
        self.pause_btn.bind(on_press=self.toggle_pause)
        btn_box.add_widget(self.pause_btn)
        root.add_widget(btn_box)

        # Интервал
        interval_box = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(4))
        interval_box.add_widget(Label(
            text="Интервал:", font_size=dp(11), color=DIM_COLOR,
            size_hint_x=0.3,
        ))
        for mins in (5, 15, 30, 60):
            b = Button(
                text=f"{mins}м", font_size=dp(11), bold=True,
                background_normal="",
                background_color=get_color_from_hex(
                    "#4CAF50" if self.interval_sec == mins * 60 else "#444460"
                ),
            )
            b.bind(on_press=lambda bb, m=mins: self.set_interval(m))
            interval_box.add_widget(b)
        root.add_widget(interval_box)

        root.add_widget(Label(
            text="Последние записи:",
            font_size=dp(12), bold=True, color=TEXT_COLOR,
            size_hint_y=None, height=dp(24),
        ))

        self.recent_box = BoxLayout(
            orientation="vertical", size_hint_y=1, spacing=dp(3),
        )
        root.add_widget(self.recent_box)

        features = []
        if HAS_VIBRATOR: features.append("📳")
        if HAS_NOTIF:    features.append("🔔")
        features_str = " ".join(features) if features else "—"

        root.add_widget(Label(
            text=f"v{VERSION}  •  {features_str}",
            font_size=dp(10), color=get_color_from_hex("#444460"),
            size_hint_y=None, height=dp(18),
        ))

        Clock.schedule_once(lambda dt: self.refresh_recent(), 0.5)
        Clock.schedule_interval(self.tick, 1.0)

        return root

    def _update_bg(self, instance, value):
        self._bg.pos = instance.pos
        self._bg.size = instance.size

    def tick(self, dt):
        if self.paused or self.ask_popup is not None:
            return
        now = time.time()
        elapsed = now - self.last_ask_time
        if elapsed >= self.interval_sec:
            self.ask_now()
            self.last_ask_time = now
            self.data["last_ask_time"] = now
            save_data(self.data)
        else:
            remaining = int(self.interval_sec - elapsed)
            mm = remaining // 60
            ss = remaining % 60
            self.timer_label.text = f"{mm:02d}:{ss:02d}"

    def reset_timer(self):
        self.last_ask_time = time.time()
        self.data["last_ask_time"] = self.last_ask_time
        save_data(self.data)

    def force_ask(self):
        if self.ask_popup is not None:
            return
        self.ask_now()
        self.last_ask_time = time.time()
        self.data["last_ask_time"] = self.last_ask_time
        save_data(self.data)

    def ask_now(self):
        signal_attention()
        self.ask_popup = AskPopup(self)
        self.ask_popup.open()

    def show_stats(self):
        StatsPopup(self).open()

    def toggle_pause(self, *args):
        self.paused = not self.paused
        if self.paused:
            self.status_label.text = "⏸ Пауза"
            self.status_label.color = get_color_from_hex("#FF9800")
            self.pause_btn.text = "▶"
        else:
            self.status_label.text = "Работает"
            self.status_label.color = get_color_from_hex("#4CAF50")
            self.pause_btn.text = "⏸"
            self.reset_timer()

    def set_interval(self, minutes):
        self.interval_sec = minutes * 60
        self.data["interval_min"] = minutes
        save_data(self.data)
        self.reset_timer()
        self.status_label.text = f"Интервал: {minutes} мин"
        self.status_label.color = ACCENT_COLOR

    def refresh_recent(self):
        self.recent_box.clear_widgets()
        records = self.data["records"][-5:][::-1]
        if not records:
            self.recent_box.add_widget(Label(
                text="Пока пусто. Ответь на первый вопрос.",
                font_size=dp(11), color=DIM_COLOR,
            ))
            return
        for rec in records:
            cat = rec.get("category", "other")
            info = CAT_BY_ID.get(cat, ("other", "?", "#607D8B", "?"))
            color = get_color_from_hex(info[2])
            row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(4))
            row.add_widget(Label(
                text="●", font_size=dp(16), color=color,
                size_hint_x=None, width=dp(22),
            ))
            row.add_widget(Label(
                text=f"{info[3]} {info[1]}", font_size=dp(11),
                color=TEXT_COLOR, halign="left",
            ))
            row.add_widget(Label(
                text=rec.get("time", ""), font_size=dp(10),
                color=DIM_COLOR, halign="right", size_hint_x=0.55,
            ))
            self.recent_box.add_widget(row)

    def export_csv(self):
        csv_file = os.path.join(os.path.expanduser("~"), "zalip_log.csv")
        try:
            with open(csv_file, "w", encoding="utf-8") as f:
                f.write("time,category,comment\n")
                for rec in self.data["records"]:
                    t = rec.get("time", "")
                    c = rec.get("category", "")
                    com = rec.get("comment", "").replace(",", ";").replace("\n", " ")
                    f.write(f"{t},{c},{com}\n")
            popup = Popup(
                title="", title_size=1, separator_height=0,
                size_hint=(0.8, 0.3),
                background_color=(0, 0, 0, 0.7),
                content=Label(
                    text=f"Сохранено:\n{csv_file}",
                    font_size=dp(12), color=TEXT_COLOR,
                ),
            )
            popup.open()
            Clock.schedule_once(lambda dt: popup.dismiss(), 3)
        except Exception as e:
            print("export err:", e)

    def clear_all(self, popup):
        self.data = {"records": [],
                     "interval_min": self.data.get("interval_min", DEFAULT_INTERVAL_MIN),
                     "last_ask_time": time.time()}
        save_data(self.data)
        self.refresh_recent()
        popup.dismiss()
        self.status_label.text = "Все записи удалены"
        self.status_label.color = DIM_COLOR


if __name__ == "__main__":
    ZalipApp().run()