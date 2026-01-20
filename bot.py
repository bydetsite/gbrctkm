import os
import re
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN не установлен в окружение")

PATTERN = re.compile(
    r'gtag\("event",\s*"conversion",\s*{[^}]*"aw_id":\s*"(\d+)",\s*"awc":\s*"([^"]+)"[^}]*}\)'
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    matches = PATTERN.findall(text)
    if not matches:
        await update.message.reply_text("❌ Не найдено подходящих gtag conversion событий.")
        return

    counts = Counter(matches)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    unique = list(counts)

    lines = [f"/?aw={aw_id}&awc={awc}" for aw_id, awc in unique]
    result = "\n".join(lines)

    warn_lines = []
    for (aw_id, awc), cnt in duplicates.items():
        warn_lines.append(f"⚠️  дубль – /?aw={aw_id}&awc={awc}, встречается {cnt} раз")
    warn_text = "\n".join(warn_lines) + "\n\n" if warn_lines else ""

    keyboard = [[InlineKeyboardButton("📋 Скопировать всё", callback_data="copy")]]
    await update.message.reply_text(
        f"{warn_text}✅ Готово:\n\n<pre>{result}</pre>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    text = query.message.text or ""
    if "<pre>" in text and "</pre>" in text:
        clean = text.split("<pre>")[1].split("</pre>")[0]
    else:
        clean = text
    await query.message.reply_text(f"📋 Для копирования:\n\n{clean}")

def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^copy$"))
    app.run_polling()

if __name__ == "__main__":
    main()
