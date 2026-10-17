# SesButonu 🔊

**English** | [Türkçe](README.tr.md)

A small Linux app that plays a sound of your choice when you press a key or key combination.

- GUI: add sounds by **drag & drop** or with a file picker
- Select a sound, press **Assign Key**, then press the key/combination you want (F9, Ctrl+Alt+S, ...)
- Many sounds and keys at once; sounds can overlap, **Stop** silences them all
- Enable/disable each entry individually, or switch all listening on/off with one button
- Works while other apps are focused (global shortcuts), on **X11 and Wayland**
- Minimizes to the system tray (KDE Plasma works out of the box; GNOME needs the AppIndicator extension)
- English and Turkish interface (follows your system language; switch from the box in the top right)

## Install

```bash
git clone https://github.com/z3t0v1c2/sesbutonu.git
cd sesbutonu
bash setup.sh
```

`setup.sh` asks you for the **language** (Türkçe/English), your **distribution** (1 Arch, 2 Debian/Ubuntu, 3 Fedora, 4 Other)
and your **desktop** (1 KDE Plasma, 2 GNOME, 3 Other). Type the number and press Enter (Enter alone = detected default).
It then installs the dependencies, adds you to the `input` group, installs the app into `~/.local/share/sesbutonu`
and adds a **SesButonu** menu entry. Choosing GNOME also installs the AppIndicator extension for the tray icon.

> **Important:** if you were just added to the `input` group, **log out and back in** afterwards.
> Otherwise key assignment and listening won't work. Check with `groups` — it should list `input`.

Start: `sesbutonu` (or from the app menu). Uninstall: `bash setup.sh --uninstall`

### Manual install (Arch Linux)

```bash
sudo pacman -S python-evdev pyside6 mpv
sudo usermod -aG input $USER   # then log out and back in
python sesbutonu.py
```

Or build a package: `makepkg -si`

## Usage

1. Drag sound files onto the window or press **＋ Add Sound**.
2. Select a sound → **⌨ Assign Key** (or double-click) → press the key or combination.
3. While the big green button says **LISTENING ON**, the keys play their sounds. Click it to turn listening off.
4. Closing the window keeps the app running in the tray. Use the tray menu's **Quit** to exit.

Settings are stored in `~/.config/sesbutonu/ayarlar.json`.
Start hidden in the tray: `sesbutonu --gizli`

> Keys are not "swallowed": the key still reaches other apps. Avoid combinations that clash
> with your desktop's own shortcuts (e.g. use `F9` or `Ctrl+Alt+...`).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cannot access keyboard devices" / keys can't be assigned | Run `bash setup.sh` (or `sudo usermod -aG input $USER`) and **log out and back in**; `groups` must list `input` |
| No sound | Install `mpv` |
| No tray icon on GNOME | Enable the AppIndicator extension (setup.sh does this; re-login) |
---

<img width="671" height="514" alt="test2" src="https://github.com/user-attachments/assets/c2ee9d7a-f722-4175-a131-7b3d319296fc" />

---

## License

MIT - see [LICENSE](LICENSE)
