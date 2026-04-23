"""
Handler generate gambar dari link produk atau foto yang diupload
"""

import os
import re
import time
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.scraper import scraper
from services.image_gen import image_generator
from services.database import db
from config import config

URL_PATTERN = re.compile(r'https?://[^\s]+')


def is_product_url(text: str) -> bool:
    platforms = ["tiktok.com", "shopee.co.id", "tokopedia.com",
                 "lazada.co.id", "tokopedia.link", "vt.tiktok.com"]
    return any(p in text for p in platforms) and bool(URL_PATTERN.search(text))


async def handle_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle perintah /generate atau pesan berisi link produk"""
    message = update.message
    user = update.effective_user
    text = message.text or ""

    # Ambil URL dari pesan atau argumen command
    if context.args:
        text = " ".join(context.args)

    url_match = URL_PATTERN.search(text)

    if not url_match and not is_product_url(text):
        await message.reply_text(
            "🔗 Kirim link produk TikTok/Shopee/Tokopedia untuk generate gambar\\.\n\n"
            "Contoh:\n"
            "`/generate https://shopee.co.id/produk-saya`\n\n"
            "Atau langsung paste linknya di chat\\!",
            parse_mode="MarkdownV2"
        )
        return

    url = url_match.group(0) if url_match else text.strip()

    # Simpan URL di context untuk dipakai handler lain
    context.user_data["last_url"] = url
    context.user_data["last_user_id"] = user.id

    # Tanya user mau generate apa
    keyboard = [
        [
            InlineKeyboardButton("📸 Gambar Saja", callback_data=f"gen_image"),
            InlineKeyboardButton("🎬 Gambar + Video", callback_data=f"gen_image_video"),
        ],
        [
            InlineKeyboardButton("✍️ Caption Saja", callback_data=f"gen_caption"),
            InlineKeyboardButton("🚀 Lengkap (Semua)", callback_data=f"gen_all"),
        ],
    ]

    status_msg = await message.reply_text(
        "🔍 Link produk diterima\\! Pilih yang ingin di-generate:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    context.user_data["status_msg_id"] = status_msg.message_id


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle foto yang diupload langsung oleh user"""
    message = update.message
    user = update.effective_user

    # Ambil foto ukuran terbesar
    photo = message.photo[-1]

    status = await message.reply_text("📥 Foto diterima, memproses...")

    # Download foto
    photo_file = await photo.get_file()
    temp_dir = Path(config.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    photo_path = str(temp_dir / f"upload_{user.id}_{int(time.time())}.jpg")
    await photo_file.download_to_drive(photo_path)

    context.user_data["uploaded_photo"] = photo_path

    keyboard = [
        [
            InlineKeyboardButton("🎬 Buat Video dari Foto ini", callback_data="photo_to_video"),
            InlineKeyboardButton("✍️ Generate Caption", callback_data="photo_to_caption"),
        ],
    ]

    await status.edit_text(
        "✅ Foto berhasil diupload\\! Mau dibuat apa?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def run_generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              url: str, user_id: int) -> tuple:
    """
    Core function: scrape produk → generate prompt → generate gambar
    Returns (image_path, product_info)
    """
    chat_id = update.effective_chat.id

    # Step 1: Scrape info produk
    status = await context.bot.send_message(chat_id, "🔍 Mengambil info produk...")
    product = await scraper.scrape(url)

    await status.edit_text(f"✅ Produk ditemukan: *{product.name[:50]}*", parse_mode="Markdown")

    # Step 2: Generate prompt
    status2 = await context.bot.send_message(chat_id, "🧠 Membuat prompt gambar...")
    prompt = await image_generator.generate_prompt(product.to_prompt())
    await status2.edit_text(f"✅ Prompt siap: `{prompt[:80]}...`", parse_mode="Markdown")

    # Step 3: Generate gambar
    status3 = await context.bot.send_message(chat_id, "🎨 Generating gambar produk... (30-60 detik)")
    temp_dir = Path(config.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    image_path = str(temp_dir / f"img_{user_id}_{int(time.time())}.png")

    await image_generator.generate(prompt, image_path)
    await status3.edit_text("✅ Gambar berhasil di-generate!")

    # Simpan ke database
    db.save_history(user_id, "image", url, image_path, prompt)
    context.user_data["last_image_path"] = image_path
    context.user_data["last_product"] = product
    context.user_data["last_prompt"] = prompt

    return image_path, product
