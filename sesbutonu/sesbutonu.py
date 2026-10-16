#!/usr/bin/env python3
"""SesButonu - ses dosyalarına tuş ata; tuşa basınca ses çalsın (Linux, X11 + Wayland)."""
import json
import os
import select
import shutil
import subprocess
import sys

try:
    import evdev
    from evdev import ecodes
except ImportError:
    sys.exit("evdev eksik. Kur:  pip install evdev")

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QHBoxLayout,
                               QHeaderView, QLabel, QMenu, QMessageBox, QPushButton, QSystemTrayIcon,
                               QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

CONFIG = os.path.expanduser("~/.config/sesbutonu/ayarlar.json")
AUDIO = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".opus", ".aac")
MODS = {
    "ctrl": {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL},
    "alt": {ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT},
    "shift": {ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT},
    "super": {ecodes.KEY_LEFTMETA, ecodes.KEY_RIGHTMETA},
}
MOD_CODES = set().union(*MODS.values())
PLAYERS = [
    ["mpv", "--no-video", "--really-quiet"],
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
    ["paplay"], ["pw-play"], ["aplay", "-q"],
]

LANG = "tr"
TXT = {
    "hint": ("Ses dosyalarını pencereye sürükleyip bırak veya «Ses Ekle»ye bas.\nListeden birini seç ve «Tuş Ata»ya bas (çift tıklamak da olur). Pencereyi kapatırsan sistem tepsisine küçülür.",
             "Drag & drop sound files onto the window or press “Add Sound”.\nSelect one in the list and press “Assign Key” (double-click works too). Closing the window minimizes it to the system tray."),
    "col_on": ("Açık", "On"), "col_sound": ("Ses dosyası", "Sound file"), "col_key": ("Tuş", "Key"),
    "b_add": ("＋ Ses Ekle", "＋ Add Sound"), "b_assign": ("⌨ Tuş Ata", "⌨ Assign Key"),
    "b_test": ("▶ Dene", "▶ Test"), "b_stop": ("■ Durdur", "■ Stop"), "b_del": ("🗑 Sil", "🗑 Delete"),
    "tray_show": ("Göster", "Show"), "tray_listen": ("Dinleme açık", "Listening on"), "tray_quit": ("Çık", "Quit"),
    "unassigned": ("— atanmadı —", "— not assigned —"),
    "file_title": ("Ses dosyası seç", "Choose sound file"),
    "file_filter": ("Ses dosyaları (*.mp3 *.wav *.ogg *.flac *.m4a *.opus *.aac)",
                    "Sound files (*.mp3 *.wav *.ogg *.flac *.m4a *.opus *.aac)"),
    "pick_first": ("Önce listeden bir ses seç.", "Select a sound in the list first."),
    "assign_title": ("Tuş ata", "Assign key"),
    "assign_text": ("«{}» için\ntuşa veya kombinasyona bas (örn. F9, Ctrl+Alt+S).\nBıraktığında kaydedilir. İptal: Esc",
                    "Press a key or key combination for\n“{}”\n(e.g. F9, Ctrl+Alt+S). It is saved when you release it. Cancel: Esc"),
    "cancel": ("İptal", "Cancel"),
    "on": ("● DİNLEME AÇIK (kapatmak için tıkla)", "● LISTENING ON (click to turn off)"),
    "off": ("○ DİNLEME KAPALI (açmak için tıkla)", "○ LISTENING OFF (click to turn on)"),
    "no_player": ("Ses oynatıcı (mpv) bulunamadı. Lütfen mpv kur.", "No audio player found. Please install mpv."),
    "no_kbd": ("Klavye cihazlarına erişilemiyor, bu yüzden tuş atanamaz ve tuşlar dinlenemez.\n\nÇözüm: bash setup.sh çalıştır (veya: sudo usermod -aG input $USER) ve oturumu kapatıp tekrar aç.\n\nKontrol: terminalde `groups` yazınca listede 'input' görünmeli.",
               "Cannot access keyboard devices, so keys can't be assigned or listened to.\n\nFix: run bash setup.sh (or: sudo usermod -aG input $USER) and log out and back in.\n\nCheck: `groups` in a terminal should list 'input'."),
}


def t(k):
    return TXT[k][0 if LANG == "tr" else 1]


def detect_lang():
    loc = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "").lower()
    return "tr" if loc.startswith("tr") else "en"


def load():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            d = json.load(f)
        return {"enabled": d.get("enabled", True), "items": d.get("items", []), "lang": d.get("lang")}
    except (OSError, ValueError, AttributeError):
        return {"enabled": True, "items": [], "lang": None}


def save(cfg):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def code_name(c):
    n = ecodes.KEY.get(c) or f"KEY_{c}"
    return (n[0] if isinstance(n, list) else n)[4:].lower()


def combo_from(codes):
    mods = [m for m, cs in MODS.items() if cs & codes]
    return "+".join(mods + sorted(code_name(c) for c in codes - MOD_CODES))


def parse(combo):
    parts = combo.split("+")
    mods = [MODS[p] for p in parts if p in MODS]
    keys = {ecodes.ecodes.get("KEY_" + p.upper()) for p in parts if p not in MODS}
    return (mods, keys) if keys and None not in keys else None


def keyboards():
    devs = []
    for p in evdev.list_devices():
        try:
            d = evdev.InputDevice(p)
        except OSError:
            continue
        caps = d.capabilities().get(ecodes.EV_KEY, [])
        if ecodes.KEY_A in caps and ecodes.KEY_ENTER in caps:
            devs.append(d)
    return devs


class Listener(QThread):
    """Arka planda klavyeyi dinler; kısayol eşleşince sesi çalar."""
    captured = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.bindings, self.procs = [], []
        self.enabled, self.capturing, self.alive = True, False, True
        self.err = ""

    def set_items(self, items):
        b = []
        for it in items:
            p = parse(it["key"]) if it.get("key") and it.get("enabled") else None
            if p:
                b.append((p, it["path"]))
        self.bindings = b

    def play(self, path):
        if not os.path.isfile(path):
            return
        for cmd in PLAYERS:
            if shutil.which(cmd[0]):
                self.procs = [p for p in self.procs if p.poll() is None]
                self.procs.append(subprocess.Popen(cmd + [path], stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.DEVNULL))
                return
        self.error.emit(t("no_player"))

    def stop_all(self):
        for p in self.procs:
            if p.poll() is None:
                p.terminate()
        self.procs = []

    def run(self):
        devs = keyboards()
        if not devs:
            self.err = t("no_kbd")
            self.error.emit(self.err)
            return
        fds = {d.fd: d for d in devs}
        pressed, peak = set(), set()
        while self.alive:
            ready, _, _ = select.select(list(fds), [], [], 0.5)
            for fd in ready:
                try:
                    events = list(fds[fd].read())
                except BlockingIOError:
                    continue
                except OSError:
                    del fds[fd]
                    continue
                for ev in events:
                    if ev.type != ecodes.EV_KEY or ev.value == 2:
                        continue
                    if ev.value == 1:
                        pressed.add(ev.code)
                        if self.capturing:
                            peak |= pressed
                        elif self.enabled:
                            for (mods, keys), path in self.bindings:
                                if ev.code in keys and keys <= pressed and all(m & pressed for m in mods):
                                    self.play(path)
                    else:
                        pressed.discard(ev.code)
                        if not pressed:
                            if self.capturing and peak - MOD_CODES:
                                self.capturing = False
                                self.captured.emit(combo_from(peak))
                            peak = set()


class Win(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SesButonu")
        self.resize(680, 500)
        self.setAcceptDrops(True)
        self.cfg = load()
        self.items = self.cfg["items"]
        self.dlg = None
        self.cap_row = -1
        self.quitting = False

        self.ls = Listener()
        self.ls.captured.connect(self.on_captured)
        self.ls.error.connect(self.on_error)

        hint = QLabel(t("hint"))
        hint.setWordWrap(True)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([t("col_on"), t("col_sound"), t("col_key")])
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemChanged.connect(self.on_check)
        self.table.cellDoubleClicked.connect(lambda r, c: self.assign())

        row = QHBoxLayout()
        for text, fn in [(t("b_add"), self.add_dialog), (t("b_assign"), self.assign),
                         (t("b_test"), self.test), (t("b_stop"), self.ls.stop_all),
                         (t("b_del"), self.remove)]:
            b = QPushButton(text)
            b.clicked.connect(lambda _=False, f=fn: f())
            row.addWidget(b)

        self.toggle = QPushButton()
        self.toggle.setCheckable(True)
        self.toggle.setMinimumHeight(40)
        self.toggle.toggled.connect(self.on_toggle)
        self.msg = QLabel("")
        self.msg.setWordWrap(True)

        lay = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(hint, 1)
        self.lang = QComboBox()
        self.lang.addItem("Türkçe", "tr")
        self.lang.addItem("English", "en")
        self.lang.setCurrentIndex(0 if LANG == "tr" else 1)
        self.lang.currentIndexChanged.connect(self.change_lang)
        top.addWidget(self.lang, 0, Qt.AlignTop)
        lay.addLayout(top)
        lay.addWidget(self.table)
        lay.addLayout(row)
        lay.addWidget(self.toggle)
        lay.addWidget(self.msg)

        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(QIcon.fromTheme("audio-x-generic"), self)
            menu = QMenu(self)
            menu.addAction(t("tray_show"), self.show_win)
            self.act = menu.addAction(t("tray_listen"))
            self.act.setCheckable(True)
            self.act.toggled.connect(self.toggle.setChecked)
            menu.addAction(t("tray_quit"), self.quit_app)
            self.tray.setContextMenu(menu)
            self.tray.activated.connect(
                lambda r: self.show_win() if r == QSystemTrayIcon.Trigger else None)
            self.tray.show()

        self.toggle.setChecked(self.cfg["enabled"])
        self.on_toggle(self.cfg["enabled"])
        self.commit()
        self.ls.start()

    # --- veri ---
    def commit(self):
        save(self.cfg)
        self.ls.set_items(self.items)
        cur = self.table.currentRow()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.items))
        for i, it in enumerate(self.items):
            c0 = QTableWidgetItem()
            c0.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            c0.setCheckState(Qt.Checked if it["enabled"] else Qt.Unchecked)
            c1 = QTableWidgetItem(os.path.basename(it["path"]))
            c1.setToolTip(it["path"])
            key = it["key"].upper().replace("+", " + ") if it["key"] else t("unassigned")
            self.table.setItem(i, 0, c0)
            self.table.setItem(i, 1, c1)
            self.table.setItem(i, 2, QTableWidgetItem(key))
        self.table.blockSignals(False)
        if 0 <= cur < len(self.items):
            self.table.selectRow(cur)

    def add_files(self, paths):
        known = {it["path"] for it in self.items}
        for p in paths:
            if p.lower().endswith(AUDIO) and p not in known:
                self.items.append({"path": p, "key": "", "enabled": True})
        self.commit()
        self.table.selectRow(len(self.items) - 1)

    # --- olaylar ---
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.add_files([u.toLocalFile() for u in e.mimeData().urls()])

    def add_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, t("file_title"), os.path.expanduser("~"), t("file_filter"))
        self.add_files(files)

    def selected(self):
        r = self.table.currentRow()
        if r < 0:
            self.msg.setText(t("pick_first"))
        else:
            self.msg.setText("")
        return r

    def on_error(self, m):
        self.msg.setText("⚠ " + m.split("\n")[0])
        self.box = QMessageBox(QMessageBox.Warning, "SesButonu", m, parent=self)
        self.box.open()

    def assign(self):
        r = self.selected()
        if r < 0:
            return
        if self.ls.err:
            self.on_error(self.ls.err)
            return
        self.cap_row = r
        dlg = self.dlg = QDialog(self)
        dlg.setWindowTitle(t("assign_title"))
        v = QVBoxLayout(dlg)
        v.addWidget(QLabel(t("assign_text").format(os.path.basename(self.items[r]["path"]))))
        cancel = QPushButton(t("cancel"))
        cancel.setAutoDefault(False)
        cancel.setFocusPolicy(Qt.NoFocus)
        cancel.clicked.connect(dlg.reject)
        v.addWidget(cancel)
        self.ls.capturing = True
        dlg.exec()
        self.ls.capturing = False
        self.dlg = None

    def on_captured(self, key):
        if self.dlg:
            self.items[self.cap_row]["key"] = key
            self.commit()
            self.dlg.accept()

    def on_check(self, item):
        if item.column() == 0:
            self.items[item.row()]["enabled"] = item.checkState() == Qt.Checked
            self.commit()

    def test(self):
        r = self.selected()
        if r >= 0:
            self.ls.play(self.items[r]["path"])

    def remove(self):
        r = self.selected()
        if r >= 0:
            del self.items[r]
            self.commit()

    def on_toggle(self, on):
        self.cfg["enabled"] = on
        self.ls.enabled = on
        if self.tray:
            self.act.setChecked(on)
        self.toggle.setText(t("on") if on
                            else t("off"))
        self.toggle.setStyleSheet("background:#2e7d32;color:white;font-weight:bold;" if on
                                  else "background:#777;color:white;font-weight:bold;")
        save(self.cfg)

    def show_win(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def change_lang(self, i):
        self.cfg["lang"] = self.lang.itemData(i)
        save(self.cfg)
        self.ls.alive = False
        self.ls.stop_all()
        self.ls.wait(1500)
        os.execv(sys.executable, [sys.executable] + [a for a in sys.argv if a != "--gizli"])

    def quit_app(self):
        self.quitting = True
        self.close()

    def closeEvent(self, e):
        if self.tray and not self.quitting:
            e.ignore()
            self.hide()
            return
        self.ls.alive = False
        self.ls.stop_all()
        self.ls.wait(1500)
        e.accept()
        QApplication.quit()


def main():
    global LANG
    LANG = load().get("lang") or detect_lang()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = Win()
    if not (w.tray and "--gizli" in sys.argv):
        w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
