"""
Handler generate caption TikTok
"""

import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.scraper import scraper
from services.caption_gen import caption_generator
from services.database import db

URL_PATTERN = re.compile(r'https?://[^\s]+')


async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle perintah /caption [link atau deskripsi]"""
    message = update.message
    user = update.effective_user

    if not context.args:
        await message.reply_text(
            "✍️ *Generate Caption TikTok*\n\n"
            "Cara penggunaan:\n"
            "`/caption [link produk]`\n"
            "`/caption [deskripsi produk]`\n\n"
            "Contoh:\n"
            "`/caption https://shopee.co.id/...`\n"
            "`/caption Serum Vitamin C 30ml brightening wajah glowing`",
            parse_mode="Markdown"
        )
        return

    input_text = " ".join(context.args)
    await run_generate_caption(update, context, input_text, user.id)


async def run_generate_caption(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                input_text: str, user_id: int, style: str = "engaging"):
    """Core function: generate caption dari link atau deskripsi produk"""
    chat_id = update.effective_chat.id

    status = await context.bot.send_message(chat_id, "✍️ Membuat caption TikTok...")

    try:
        # Cek apakah input adalah URL
        url_match = URL_PATTERN.search(input_text)
        if url_match:
            url = url_match.group(0)
            product = context.user_data.get("last_product") or await scraper.scrape(url)
            product_info = product.to_prompt()
            product_name = product.name
        else:
            # Input adalah deskripsi teks langsung
            product_info = input_text
            product_name = input_text[:50]

        # Generate berbagai style caption sekaligus
        await status.edit_text("✍️ Membuat beberapa variasi caption...")

        # Generate 2 style berbeda
        caption_main = await caption_generator.generate(product_info, style)
        caption_viral = await caption_generator.generate(product_info, "viral")

        # Kirim caption pertama
        text1 = caption_generator.format_for_telegram(caption_main, product_name)
        keyboard = [
            [
                InlineKeyboardButton("🔄 Regenerate", callback_data="regen_caption"),
                InlineKeyboardButton("💫 Style Viral", callback_data="caption_viral"),
            ],
            [
                InlineKeyboardButton("📋 Review Style", callback_data="caption_review"),
                InlineKeyboardButton("🔥 Style Promo", callback_data="caption_promo"),
            ],
        ]

        await status.edit_text("✅ Caption siap!")
        await context.bot.send_message(
            chat_id,
            text1,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        # Simpan ke context dan database
        context.user_data["last_caption"] = caption_main
        context.user_data["last_caption_viral"] = caption_viral
        context.user_data["last_product_info"] = product_info
        context.user_data["last_product_name"] = product_name
        db.save_history(user_id, "caption", input_text, None, caption_main.get("full_caption", ""))

    except Exception as e:
        await status.edit_text(f"❌ Gagal generate caption: {str(e)}")
