"""
Bot Telegram Affiliate TikTok
Fitur: Generate gambar produk, buat video dari gambar, generate caption TikTok
"""

import logging
import os
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from handlers.commands import start, help_cmd, history
from handlers.generate import handle_generate, handle_photo
from handlers.video import handle_video
from handlers.caption import handle_caption
from handlers.callbacks import handle_callback

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN tidak ditemukan di environment variables!")

    app = Application.builder().token(token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("generate", handle_generate))
    app.add_handler(CommandHandler("video", handle_video))
    app.add_handler(CommandHandler("caption", handle_caption))
    app.add_handler(CommandHandler("history", history))

    # Message handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_generate))

    # Callback query handler (untuk inline keyboard)
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Bot TikTok Affiliate dimulai...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
