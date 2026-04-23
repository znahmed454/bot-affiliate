"""
Handler untuk semua callback dari inline keyboard button
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.caption_gen import caption_generator


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router utama untuk semua callback query"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user

    # ─── Menu utama ───
    if data == "menu_generate":
        await query.message.reply_text(
            "📸 Kirim link produk TikTok/Shopee/Tokopedia\\.\n"
            "Atau ketik `/generate [link]`",
            parse_mode="MarkdownV2"
        )
    elif data == "menu_video":
        await query.message.reply_text(
            "🎬 Ketik `/video [link produk]` untuk generate video\\.\n"
            "Atau upload foto produk terlebih dahulu\\.",
            parse_mode="MarkdownV2"
        )
    elif data == "menu_caption":
        await query.message.reply_text(
            "✍️ Ketik `/caption [link atau deskripsi produk]`\\.",
            parse_mode="MarkdownV2"
        )
    elif data == "menu_history":
        from handlers.commands import history
        await history(update, context)
    elif data == "menu_help":
        from handlers.commands import help_cmd
        await help_cmd(update, context)

    # ─── Generate actions ───
    elif data == "gen_image":
        url = context.user_data.get("last_url")
        if not url:
            await query.message.reply_text("⚠️ Link produk tidak ditemukan. Kirim ulang linknya.")
            return
        await _do_generate_image(update, context, url, user.id)

    elif data == "gen_image_video":
        url = context.user_data.get("last_url")
        if not url:
            await query.message.reply_text("⚠️ Link produk tidak ditemukan.")
            return
        from handlers.generate import run_generate_image
        image_path, product = await run_generate_image(update, context, url, user.id)

        # Kirim gambar dulu
        with open(image_path, "rb") as img:
            await query.message.reply_photo(
                photo=img,
                caption=f"📸 Gambar: *{product.name[:50]}*\n\n🔄 Sekarang membuat video...",
                parse_mode="Markdown"
            )

        from handlers.video import run_generate_video_from_image
        await run_generate_video_from_image(update, context, image_path, product, user.id)

    elif data == "gen_caption":
        url = context.user_data.get("last_url")
        product = context.user_data.get("last_product")
        input_text = url or (product.to_prompt() if product else None)

        if not input_text:
            await query.message.reply_text(
                "✍️ Tidak ada produk yang aktif\\. Ketik deskripsi produk:\n"
                "`/caption nama produk dan deskripsinya`",
                parse_mode="MarkdownV2"
            )
            return
        from handlers.caption import run_generate_caption
        await run_generate_caption(update, context, input_text, user.id)

    elif data == "gen_all":
        url = context.user_data.get("last_url")
        if not url:
            await query.message.reply_text("⚠️ Link produk tidak ditemukan.")
            return

        # Gambar
        from handlers.generate import run_generate_image
        image_path, product = await run_generate_image(update, context, url, user.id)

        with open(image_path, "rb") as img:
            await query.message.reply_photo(
                photo=img,
                caption=f"📸 Gambar produk: *{product.name[:50]}*",
                parse_mode="Markdown"
            )

        # Video
        from handlers.video import run_generate_video_from_image
        await run_generate_video_from_image(update, context, image_path, product, user.id)

        # Caption
        from handlers.caption import run_generate_caption
        await run_generate_caption(update, context, product.to_prompt(), user.id)

    # ─── Photo actions ───
    elif data == "photo_to_video":
        photo_path = context.user_data.get("uploaded_photo")
        if not photo_path:
            await query.message.reply_text("⚠️ Foto tidak ditemukan. Upload ulang foto.")
            return

        class MockProduct:
            name = "produk"
            def to_prompt(self): return "product"

        from handlers.video import run_generate_video_from_image
        await run_generate_video_from_image(update, context, photo_path, MockProduct(), user.id)

    elif data == "photo_to_caption":
        await query.message.reply_text(
            "✍️ Deskripsikan produk ini untuk caption:\n"
            "`/caption nama dan keunggulan produk`",
            parse_mode="Markdown"
        )

    # ─── Caption style actions ───
    elif data in ("regen_caption", "caption_viral", "caption_review", "caption_promo"):
        style_map = {
            "regen_caption": "engaging",
            "caption_viral": "viral",
            "caption_review": "review",
            "caption_promo": "promo",
        }
        style = style_map[data]
        product_info = context.user_data.get("last_product_info")
        product_name = context.user_data.get("last_product_name", "")

        if not product_info:
            await query.message.reply_text("⚠️ Tidak ada produk aktif untuk di-regenerate.")
            return

        await query.message.reply_text(f"🔄 Membuat caption style *{style}*...", parse_mode="Markdown")
        caption = await caption_generator.generate(product_info, style)
        text = caption_generator.format_for_telegram(caption, product_name)

        keyboard = [
            [
                InlineKeyboardButton("🔄 Engaging", callback_data="regen_caption"),
                InlineKeyboardButton("💫 Viral", callback_data="caption_viral"),
            ],
            [
                InlineKeyboardButton("📋 Review", callback_data="caption_review"),
                InlineKeyboardButton("🔥 Promo", callback_data="caption_promo"),
            ],
        ]
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    else:
        await query.message.reply_text(f"⚠️ Aksi tidak dikenal: {data}")


async def _do_generate_image(update, context, url, user_id):
    """Helper: generate gambar dan kirim ke user"""
    from handlers.generate import run_generate_image
    image_path, product = await run_generate_image(update, context, url, user_id)

    keyboard = [
        [
            InlineKeyboardButton("🎬 Buat Video", callback_data="gen_image_video"),
            InlineKeyboardButton("✍️ Generate Caption", callback_data="gen_caption"),
        ]
    ]

    with open(image_path, "rb") as img:
        await context.bot.send_photo(
            update.effective_chat.id,
            photo=img,
            caption=f"📸 *{product.name[:80]}*\n\n{product.summary()}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
