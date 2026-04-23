# 🤖 Bot Telegram Affiliate TikTok

Bot Telegram lengkap untuk konten affiliate TikTok — generate gambar produk, buat video, dan caption viral secara otomatis dari link produk.

---

## ✨ Fitur

| Fitur | Deskripsi |
|-------|-----------|
| 📸 **Generate Gambar** | Generate gambar produk berkualitas tinggi dari link TikTok/Shopee/Tokopedia |
| 🎬 **Generate Video** | Ubah gambar menjadi video TikTok (portrait 9:16) via Kling AI atau RunwayML |
| ✍️ **Generate Caption** | Caption TikTok viral dengan hook, CTA, dan hashtag dalam Bahasa Indonesia |
| 🚀 **Paket Lengkap** | Satu link → otomatis generate gambar + video + caption |
| 📊 **History** | Simpan semua hasil generate per user |

---

## 🛠️ Setup & Instalasi

### 1. Clone & Install Dependencies

```bash
git clone <repo-url>
cd tiktok-affiliate-bot
pip install -r requirements.txt
```

### 2. Buat Bot Telegram

1. Buka [@BotFather](https://t.me/BotFather) di Telegram
2. Ketik `/newbot` dan ikuti instruksi
3. Salin **Bot Token** yang diberikan

### 3. Daftar API Keys

#### 🎨 Replicate AI (Generate Gambar) - **GRATIS untuk trial**
1. Daftar di [replicate.com](https://replicate.com)
2. Buka Settings → API Tokens → Create Token
3. Copy token

#### 🎬 Kling AI (Generate Video) - **RECOMMENDED**
1. Daftar di [klingai.com](https://klingai.com) atau [platform.klingai.com](https://platform.klingai.com)
2. Buka API Management
3. Buat API Key dan Access Key

#### 🤖 Anthropic Claude (Generate Caption) - **TERBAIK untuk Bahasa Indonesia**
1. Daftar di [console.anthropic.com](https://console.anthropic.com)
2. Buka API Keys → Create Key
3. Copy key

### 4. Konfigurasi .env

```bash
cp .env.example .env
```

Edit file `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
REPLICATE_API_TOKEN=r8_xxxx...
KLING_API_KEY=your_kling_key
KLING_ACCESS_KEY=your_kling_access_key
ANTHROPIC_API_KEY=sk-ant-xxxx...
```

### 5. Jalankan Bot

```bash
python bot.py
```

---

## 📱 Cara Penggunaan

### Cara Paling Mudah
Paste saja link produk langsung ke chat bot → pilih yang mau di-generate!

```
https://shopee.co.id/Serum-Vitamin-C-i.123.456
```

### Perintah Lengkap

| Perintah | Fungsi |
|----------|--------|
| `/start` | Mulai bot & lihat menu |
| `/generate [link]` | Generate gambar dari link produk |
| `/video [link]` | Generate video dari link produk |
| `/caption [link/deskripsi]` | Generate caption TikTok |
| `/history` | Lihat history generate |
| `/help` | Panduan penggunaan |

### Contoh Penggunaan

```bash
# Generate gambar dari Shopee
/generate https://shopee.co.id/produk-saya

# Generate caption dari deskripsi
/caption Serum Vitamin C 30ml brightening kulit glowing

# Generate semua dari TikTok Shop
/generate https://vt.tiktok.com/ZS...
```

---

## 🏗️ Struktur Proyek

```
tiktok-affiliate-bot/
├── bot.py                    # Entry point utama
├── config.py                 # Konfigurasi terpusat
├── requirements.txt
├── .env.example
├── handlers/
│   ├── commands.py           # /start, /help, /history
│   ├── generate.py           # Handler generate gambar
│   ├── video.py              # Handler generate video
│   ├── caption.py            # Handler generate caption
│   └── callbacks.py          # Inline keyboard callbacks
└── services/
    ├── scraper.py            # Scraper info produk
    ├── image_gen.py          # Replicate / DALL-E API
    ├── video_gen.py          # Kling AI / RunwayML API
    ├── caption_gen.py        # Claude / OpenAI caption
    └── database.py           # SQLite storage
```

---

## 💰 Estimasi Biaya API

| Layanan | Harga | Keterangan |
|---------|-------|------------|
| Replicate (SDXL) | ~$0.002/gambar | Sangat murah |
| Kling AI (5 detik) | ~$0.14/video | Paling worth |
| Claude API | ~$0.01/caption | Murah & akurat |
| **Total per konten** | **~$0.15** | Gambar+Video+Caption |

---

## ⚠️ Catatan Penting

- **Video** membutuhkan 1-5 menit untuk selesai — normal, API-nya memang memerlukan waktu render
- **Shopee/TikTok** terkadang memblokir scraping — jika gagal, coba upload foto produk langsung
- Bot menggunakan **async** sehingga bisa melayani banyak user sekaligus
- Semua file temp disimpan di folder `./temp/` — bersihkan berkala

---

## 🔧 Troubleshooting

**Bot tidak merespons:**
```bash
# Cek token
echo $TELEGRAM_BOT_TOKEN
python -c "from config import config; print(config.TELEGRAM_BOT_TOKEN)"
```

**Error generate gambar:**
- Pastikan `REPLICATE_API_TOKEN` valid
- Cek saldo Replicate di dashboard

**Video gagal dibuat:**
- Pastikan `KLING_API_KEY` dan `KLING_ACCESS_KEY` keduanya diisi
- Alternatif: isi `RUNWAY_API_SECRET` untuk RunwayML

---

## 📄 Lisensi

MIT License - bebas digunakan dan dimodifikasi untuk keperluan pribadi maupun komersial.
