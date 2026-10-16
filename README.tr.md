[English](README.md) | **Türkçe**

# SesButonu 🔊

Ses dosyalarına tuş (veya tuş kombinasyonu) atayıp, o tuşa basınca sesi çalan küçük bir Linux uygulaması.

- Pencere arayüzü: ses dosyalarını **sürükle-bırak** veya **dosya seç** ile ekle
- Seçtiğin sese **«Tuş Ata»** ile tuş/kombinasyon ata (F9, Ctrl+Alt+S, ...)
- Birden fazla ses ve tuş aynı anda tanımlı olabilir; sesler üst üste çalabilir
- Her satırı tek tek **açıp kapatabilir**, tüm dinlemeyi tek tuşla **durdurabilirsin**
- Başka uygulamadayken de çalışır (global kısayol), **X11 ve Wayland** destekli

## Kurulum

```bash
git clone https://github.com/KULLANICI_ADIN/sesbutonu.git
cd sesbutonu
bash setup.sh
```

`setup.sh` sana sırayla **dil** (Türkçe/English), **dağıtım** (1 Arch, 2 Debian/Ubuntu, 3 Fedora, 4 Diğer) ve
**masaüstü** (1 KDE Plasma, 2 GNOME, 3 Diğer) sorar; numarayı yazıp Enter'a basman yeterli (Enter = tahmin edilen seçenek).
Sonra bağımlılıkları kurar, kullanıcını `input` grubuna ekler, uygulamayı `~/.local/share/sesbutonu` altına
kurar ve menüye **SesButonu** kısayolunu ekler. GNOME seçersen tepsi simgesi için AppIndicator eklentisi de kurulur.

> **Önemli:** `input` grubu ilk kez ekleniyorsa kurulumdan sonra **oturumu kapatıp tekrar aç**.
> Aksi halde tuş atama ve tuş dinleme çalışmaz. Kontrol için `groups` yaz, listede `input` görünmeli.

Başlat: `sesbutonu` (veya uygulama menüsünden). Kaldırmak için: `bash setup.sh --kaldir`

Uygulama dili sistem diline göre seçilir (Türkçe veya English); pencerenin sağ üstündeki kutudan değiştirebilirsin.

### Elle kurulum (Arch Linux)

```bash
sudo pacman -S python-evdev pyside6 mpv
sudo usermod -aG input $USER   # sonra oturumu kapatıp aç
python sesbutonu.py
```

İstersen sistem paketi olarak da kurabilirsin: `makepkg -si`

## KDE Plasma notları

- Arayüz Qt ile yapıldı, Plasma'da yerel görünür; **X11 ve Wayland** oturumlarında çalışır.
- Pencereyi kapatınca program **sistem tepsisine** küçülür. Tepsi simgesine sol tıklayınca pencere açılır, sağ tıklayınca **Göster / Dinleme açık / Çık** menüsü gelir.
- Dolphin'den ses dosyalarını doğrudan pencereye sürükleyebilirsin.
- Açılışta tepside gizli başlasın:
  ```bash
  sed 's/^Exec=.*/Exec=sesbutonu --gizli/' sesbutonu.desktop > ~/.config/autostart/sesbutonu.desktop
  ```
  (Ya da `setup.sh` çalışırken sorulan soruya `e` de.) Bunu *Sistem Ayarları → Başlangıç ve Kapanış → Otomatik Başlat* bölümünden de kontrol edebilirsin.
- Program tuşları yutmadığı için Plasma'nın kendi kısayollarıyla çakışan kombinasyonlar seçme (*Sistem Ayarları → Kısayollar* bölümüne bak). `F9`, `Ctrl+Alt+Numpad...` gibi boşta olanlar iyi çalışır.

## Kullanım

1. Ses dosyalarını pencereye sürükle veya **＋ Ses Ekle**'ye bas.
2. Listeden bir ses seç → **⌨ Tuş Ata** (veya çift tıkla) → istediğin tuşa/kombinasyona bas.
3. Alttaki yeşil düğme **DİNLEME AÇIK** olduğu sürece tuşlar sesi çalar. Tıklayıp kapatabilirsin.
4. Pencereyi kapatınca program tepside çalışmaya devam eder. Tamamen kapatmak için tepsi menüsünden **Çık**'ı seç.

Ayarlar `~/.config/sesbutonu/ayarlar.json` dosyasında saklanır.

> Program tuşları "yutmaz": seçtiğin tuş başka uygulamada da normal çalışır.
> Çakışmaması için `Ctrl+Alt+...` veya F9 gibi tuşlar seçmeni öneririm.

## Sorun giderme

| Sorun | Çözüm |
|-------|-------|
| "Klavye cihazlarına erişilemiyor" uyarısı / tuş atanmıyor | `bash setup.sh` çalıştır (veya `sudo usermod -aG input $USER`) ve **oturumu kapatıp aç**; `groups` çıktısında `input` olmalı |
| Ses çıkmıyor | `sudo apt install mpv` |
| Tuş atarken hiçbir şey olmuyor | Üstteki `input` grubu adımını yaptığından emin ol |
---
![imagetr.png…]()

---
## Lisans

MIT - bkz. [LICENSE](LICENSE)
