"""
Handler generate video dari gambar
"""

import re
import time
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from services.scraper import scraper
from services.image_gen import image_generator
from services.video_gen import video_generator
from services.database import db
from config import config

URL_PATTERN = re.compile(r'https?://[^\s]+')


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle perintah /video [link]"""
    message = update.message
    user = update.effective_user

    args = context.args
    if not args:
        await message.reply_text(
            "🎬 *Cara generate video:*\n\n"
            "1. `/video [link produk]` — dari link langsung\n"
            "2. Upload foto produk → pilih 'Buat Video'\n"
            "3. Setelah generate gambar, pilih 'Buat Video'\n\n"
            "Contoh:\n`/video https://shopee.co.id/produk`",
            parse_mode="Markdown"
        )
        return

    url = args[0]
    await run_generate_video_from_url(update, context, url, user.id)


async def run_generate_video_from_url(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       url: str, user_id: int):
    """Generate video lengkap: scrape → gambar → video"""
    chat_id = update.effective_chat.id

    try:
        # Cek apakah sudah ada gambar yang di-generate sebelumnya
        existing_image = context.user_data.get("last_image_path")
        existing_product = context.user_data.get("last_product")

        if existing_image and Path(existing_image).exists():
            product = existing_product
            image_path = existing_image
            await context.bot.send_message(chat_id, "♻️ Menggunakan gambar yang sudah di-generate sebelumnya...")
        else:
            # Generate gambar dulu
            from handlers.generate import run_generate_image
            image_path, product = await run_generate_image(update, context, url, user_id)

        # Generate video dari gambar
        await run_generate_video_from_image(update, context, image_path, product, user_id)

    except Exception as e:
        await context.bot.send_message(
            chat_id,
            f"❌ Gagal generate video: {str(e)}\n\nPastikan API video sudah dikonfigurasi di .env"
        )


async def run_generate_video_from_image(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                         image_path: str, product, user_id: int):
    """Generate video dari path gambar yang sudah ada"""
    chat_id = update.effective_chat.id

    status = await context.bot.send_message(
        chat_id,
        f"🎬 Membuat video dari gambar... ({config.VIDEO_DURATION} detik)\n"
        "⏳ Proses ini membutuhkan 1-3 menit, mohon tunggu..."
    )

    temp_dir = Path(config.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    video_path = str(temp_dir / f"vid_{user_id}_{int(time.time())}.mp4")

    # Buat prompt video dari nama produk
    product_name = product.name if product else "produk"
    video_prompt = (
        f"Smooth cinematic product showcase of {product_name}, "
        "slow zoom in, professional lighting, clean background, "
        "TikTok style commercial, high quality"
    )

    await video_generator.generate(image_path, video_prompt, video_path)
    await status.edit_text("✅ Video berhasil dibuat!")

    # Kirim video ke user
    with open(video_path, "rb") as vf:
        caption = f"🎬 Video produk: *{product_name[:50]}*" if product_name else "🎬 Video produk"
        await context.bot.send_video(
            chat_id,
            video=vf,
            caption=caption,
            parse_mode="Markdown",
            supports_streaming=True
        )

    # Simpan history
    db.save_history(user_id, "video", product_name, video_path)
    context.user_data["last_video_path"] = video_path

    # Tawarkan generate caption
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [[InlineKeyboardButton("✍️ Generate Caption Sekarang", callback_data="gen_caption")]]
    await context.bot.send_message(
        chat_id,
        "🎉 Video siap\\! Mau generate caption TikTok juga?",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
