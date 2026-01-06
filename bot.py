import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PATTERN = re.compile(r"send_to'\s*:\s*'AW-(\d+)/([^']+)'")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Пришлите HTML с gtag conversion.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    matches = PATTERN.findall(text)
    if not matches:
        await update.message.reply_text("❌ Не найдено подходящих gtag conversion событий.")
        return
    unique = list(dict.fromkeys(matches))
    lines = [f"/?aw={aw_id}&awc={awc}" for aw_id, awc in unique]
    result = "\n".join(lines)
    keyboard = [[InlineKeyboardButton("📋 Скопировать всё", callback_data="copy")]]
    await update.message.reply_text(
        f"✅ Готово:\n\n<pre>{result}</pre>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    clean = query.message.text.replace("✅ Готово:\n\n<pre>", "").replace("</pre>", "")
    await query.message.reply_text(f"📋 Для копирования:\n\n{clean}")

def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
