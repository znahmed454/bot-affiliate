"""
Handler untuk perintah dasar bot
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.database import db


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.upsert_user(user.id, user.username or "", user.first_name or "")

    keyboard = [
        [
            InlineKeyboardButton("📸 Generate Gambar", callback_data="menu_generate"),
            InlineKeyboardButton("🎬 Generate Video", callback_data="menu_video"),
        ],
        [
            InlineKeyboardButton("✍️ Generate Caption", callback_data="menu_caption"),
            InlineKeyboardButton("📊 History", callback_data="menu_history"),
        ],
        [InlineKeyboardButton("❓ Bantuan", callback_data="menu_help")],
    ]

    await update.message.reply_text(
        f"👋 Halo *{user.first_name}*\\!\n\n"
        "🤖 Selamat datang di *Bot Affiliate TikTok*\\!\n\n"
        "Aku bisa membantumu:\n"
        "📸 Generate gambar produk dari link\n"
        "🎬 Buat video menarik dari gambar\n"
        "✍️ Buat caption TikTok yang viral\n\n"
        "💡 *Cara cepat:* Cukup kirim link produk TikTok/Shopee/Tokopedia ke sini\\!\n\n"
        "Pilih menu di bawah atau langsung kirim link produk:",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Panduan Bot Affiliate TikTok*\n\n"
        "*Cara penggunaan:*\n\n"
        "1️⃣ *Generate Gambar Produk*\n"
        "   Kirim link produk atau ketik `/generate [link]`\n"
        "   Contoh: `/generate https://shopee.co.id/...`\n\n"
        "2️⃣ *Generate Video*\n"
        "   Ketik `/video [link]` atau kirim gambar lalu pilih 'Buat Video'\n"
        "   Contoh: `/video https://tiktok.com/...`\n\n"
        "3️⃣ *Generate Caption*\n"
        "   Ketik `/caption [link atau deskripsi produk]`\n"
        "   Contoh: `/caption Serum Vitamin C 30ml brightening kulit`\n\n"
        "4️⃣ *Paket Lengkap (All-in-One)*\n"
        "   Cukup kirim link produk → bot akan tanya mau generate apa\n\n"
        "*Platform yang didukung:*\n"
        "✅ TikTok Shop  ✅ Shopee  ✅ Tokopedia  ✅ Lazada\n\n"
        "*Tips untuk hasil terbaik:*\n"
        "• Gunakan link produk yang valid\n"
        "• Untuk gambar kustom, upload foto produk langsung\n"
        "• Caption bisa dibuat dari deskripsi produk tanpa link"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    records = db.get_history(user_id, limit=5)
    stats = db.get_stats(user_id)

    if not records:
        await update.message.reply_text(
            "📭 Belum ada history\\. Mulai dengan mengirim link produk\\!",
            parse_mode="MarkdownV2"
        )
        return

    total = sum(stats.values())
    stats_text = " | ".join([f"{k}: {v}" for k, v in stats.items()])

    text = f"📊 *History Kamu* \\(Total: {total}\\)\n"
    text += f"_{stats_text}_\n\n"

    for i, rec in enumerate(records, 1):
        emoji = {"image": "📸", "video": "🎬", "caption": "✍️"}.get(rec["type"], "📄")
        input_short = rec["input"][:40] + "..." if len(rec["input"]) > 40 else rec["input"]
        text += f"{emoji} *{rec['type'].title()}* \\- {input_short}\n"

    await update.message.reply_text(text, parse_mode="MarkdownV2")
