#!/usr/bin/env bash
# SesButonu setup / kurulum betiği
# Uninstall / Kaldırmak için:  bash setup.sh --uninstall
set -e
cd "$(dirname "$(readlink -f "$0")")"

APP="$HOME/.local/share/sesbutonu"
BIN="$HOME/.local/bin"
DESK="$HOME/.local/share/applications"

# choose "soru" varsayılan seçenek1 seçenek2 ... -> seçilen numarayı yazdırır
choose() {
    local prompt="$1" def="$2" i=1 n
    shift 2
    echo >&2
    echo "$prompt" >&2
    for o in "$@"; do echo "  $i) $o" >&2; i=$((i + 1)); done
    while true; do
        printf "> [%s] " "$def" >&2
        read -r n || n=""
        n="${n:-$def}"
        if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le $# ]; then echo "$n"; return; fi
    done
}

# --- Dil / Language ---
case "${LANG:-}" in tr*) d=1 ;; *) d=2 ;; esac
if [ "$(choose "Dil / Language:" $d "Türkçe" "English")" = 1 ]; then L=tr; else L=en; fi
m() { if [ "$L" = tr ]; then echo "$1"; else echo "$2"; fi; }

if [ "$1" = "--kaldir" ] || [ "$1" = "--uninstall" ]; then
    rm -rf "$APP" "$BIN/sesbutonu" "$DESK/sesbutonu.desktop" "$HOME/.config/autostart/sesbutonu.desktop"
    m "SesButonu kaldırıldı. (Ayarlar ~/.config/sesbutonu içinde duruyor.)" "SesButonu removed. (Settings remain in ~/.config/sesbutonu.)"
    exit 0
fi

if [ "$(id -u)" = 0 ]; then
    m "Bu betiği root olarak değil, normal kullanıcıyla çalıştır (sudo gerekince kendisi ister)." \
      "Run this script as a normal user, not root (it asks for sudo when needed)."
    exit 1
fi

# --- Dağıtım / Distribution ---
if command -v pacman >/dev/null; then d=1; elif command -v apt >/dev/null; then d=2
elif command -v dnf >/dev/null; then d=3; else d=4; fi
DISTRO=$(choose "$(m 'Hangi dağıtımı kullanıyorsun? (numara yaz, Enter = varsayılan)' 'Which distribution do you use? (type a number, Enter = default)')" $d \
    "Arch Linux (Manjaro, EndeavourOS...)" "Debian / Ubuntu (Mint, Pop!_OS...)" "Fedora" "$(m 'Diğer' 'Other')")

# --- Masaüstü / Desktop ---
case "${XDG_CURRENT_DESKTOP:-}" in *KDE*) e=1 ;; *GNOME*) e=2 ;; *) e=3 ;; esac
DE=$(choose "$(m 'Hangi masaüstünü kullanıyorsun?' 'Which desktop environment do you use?')" $e \
    "KDE Plasma" "GNOME" "$(m 'Diğer' 'Other')")

echo
m "==> Bağımlılıklar kuruluyor" "==> Installing dependencies"
PY=python3
VENV=""
case "$DISTRO" in
1)
    PKGS="python-evdev pyside6 mpv qt6-wayland"
    [ "$DE" = 2 ] && PKGS="$PKGS gnome-shell-extension-appindicator"
    sudo pacman -S --needed --noconfirm $PKGS
    ;;
2)
    PKGS="mpv python3-venv python3-dev gcc linux-libc-dev"
    [ "$DE" = 2 ] && PKGS="$PKGS gnome-shell-extension-appindicator"
    sudo apt update && sudo apt install -y $PKGS
    VENV=1
    ;;
3)
    PKGS="mpv python3-devel gcc kernel-headers"
    [ "$DE" = 2 ] && PKGS="$PKGS gnome-shell-extension-appindicator"
    sudo dnf install -y $PKGS
    VENV=1
    ;;
*)
    m "Bu dağıtım için paketleri otomatik kuramıyorum. Şunların kurulu olduğundan emin ol: python3 (+venv, +dev başlıkları), gcc, mpv." \
      "Can't install packages automatically for this distribution. Make sure these are installed: python3 (+venv, +dev headers), gcc, mpv."
    VENV=1
    ;;
esac

mkdir -p "$APP" "$BIN" "$DESK"
cp sesbutonu.py "$APP/"

if [ -n "$VENV" ]; then
    m "==> Python ortamı hazırlanıyor (PySide6 indirmesi biraz sürebilir)" "==> Preparing Python environment (downloading PySide6 may take a while)"
    python3 -m venv "$APP/venv"
    "$APP/venv/bin/pip" install -q evdev PySide6
    PY="$APP/venv/bin/python"
fi

m "==> Başlatıcı ve menü kısayolu ekleniyor" "==> Adding launcher and menu entry"
printf '#!/bin/sh\nexec %s "%s/sesbutonu.py" "$@"\n' "$PY" "$APP" > "$BIN/sesbutonu"
chmod +x "$BIN/sesbutonu"
sed "s|^Exec=.*|Exec=$BIN/sesbutonu|" sesbutonu.desktop > "$DESK/sesbutonu.desktop"

if [ "$(choose "$(m 'Bilgisayar açılınca tepside otomatik başlasın mı?' 'Start automatically in the tray at login?')" 2 "$(m 'Evet' 'Yes')" "$(m 'Hayır' 'No')")" = 1 ]; then
    mkdir -p "$HOME/.config/autostart"
    sed "s|^Exec=.*|Exec=$BIN/sesbutonu --gizli|" sesbutonu.desktop > "$HOME/.config/autostart/sesbutonu.desktop"
fi

RELOGIN=""
if ! id -nG | grep -qw input; then
    if ! id -nG "$USER" | grep -qw input; then
        m "==> Klavyeyi dinleyebilmek için '$USER' kullanıcısı 'input' grubuna ekleniyor" "==> Adding '$USER' to the 'input' group (needed to listen to the keyboard)"
        sudo usermod -aG input "$USER"
    fi
    RELOGIN=1
fi

if [ "$DE" = 2 ]; then
    gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com 2>/dev/null || true
    RELOGIN=1
fi

echo
m "Kurulum tamam. Başlatmak için: sesbutonu  (veya uygulama menüsünden SesButonu)" "Done. Start it with: sesbutonu  (or SesButonu in the app menu)"
case ":$PATH:" in *":$BIN:"*) ;; *) m "Not: $BIN PATH'inde değil; oturumu yeniden açınca gelir veya tam yolla çalıştır: $BIN/sesbutonu" "Note: $BIN is not in your PATH yet; it will be after re-login, or run: $BIN/sesbutonu" ;; esac
if [ "$DE" = 2 ]; then
    m "GNOME: tepsi simgesi için AppIndicator eklentisi kuruldu; oturumu yeniden açınca etkinleşir (gerekirse 'Eklentiler' uygulamasından aç)." \
      "GNOME: the AppIndicator extension (for the tray icon) was installed; it activates after re-login (enable it in the 'Extensions' app if needed)."
fi
if [ -n "$RELOGIN" ]; then
    echo
    m "!! ÖNEMLİ: Oturumu kapatıp tekrar aç (veya bilgisayarı yeniden başlat). Yoksa tuş atama ve tuş dinleme ÇALIŞMAZ." \
      "!! IMPORTANT: Log out and back in (or reboot). Otherwise key assignment and key listening will NOT work."
fi
