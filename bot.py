#!/usr/bin/env python3
# bot.py
import os
import re
import pathlib
import asyncio
import signal
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# --------------------- конфиг ---------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
USERS_FILE = pathlib.Path("users.txt")
PATTERN = re.compile(r"send_to['\"]\s*:\s*['\"]AW-(\d+)/([^'\"]+)['\"]")

# --------------------- счётчики ---------------------
def load_users() -> set[int]:
    if USERS_FILE.exists():
        return {int(uid) for uid in USERS_FILE.read_text().splitlines() if uid}
    return set()

def save_user(user_id: int) -> None:
    loaded = load_users()
    if user_id not in loaded:
        USERS_FILE.write_text("\n".join(map(str, loaded | {user_id})))

def user_count() -> int:
    return len(load_users())

# --------------------- команды ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    save_user(uid)
    await update.message.reply_text("Привет! Пришлите HTML с gtag conversion.")

async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Access denied")
        return
    await update.message.reply_text(f"📊 Всего уникальных пользователей: {user_count()}")

# --------------------- основная логика ---------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = update.effective_user.id
    save_user(uid)

    text = update.message.text
    matches = PATTERN.findall(text)
    if not matches:
        await update.message.reply_text("❌ Не найдено подходящих gtag conversion событий.")
        return

    counts = Counter(matches)
    dupes = {k: v for k, v in counts.items() if v > 1}
    unique = list(counts)
    lines = [f"/?aw={aw_id}&awc={awc}" for aw_id, awc in unique]
    result = "\n".join(lines)

    warn = "\n".join(f"⚠️  дубль – /?aw={aw}&awc={awc}, встречается {c} раз" for (aw, awc), c in dupes.items())
    if warn:
        warn += "\n\n"

    keyboard = [[InlineKeyboardButton("📋 Скопировать всё", callback_data="copy")]]
    await update.message.reply_text(
        f"{warn}✅ Готово:\n\n<pre>{result}</pre>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    clean = query.message.text.split("✅ Готово:\n\n<pre>")[-1].replace("</pre>", "")
    await query.message.reply_text(f"📋 Для копирования:\n\n{clean}")

# --------------------- запуск ---------------------
def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stat", stat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    loop = asyncio.get_event_loop()
    stop_event = asyncio.Event()

    def _shutdown():
        print("[info] Получен сигнал завершения")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _shutdown)

    # НЕ ставим drop_pending_updates=True – чтобы бот «догонял» сообщения
    app.run_polling(
        close_loop=False,
        stop_signal=None
    )

    try:
        loop.run_until_complete(stop_event.wait())
    finally:
        print("[info] Штатный shutdown")
        loop.run_until_complete(app.shutdown())
        loop.close()

if __name__ == "__main__":
    main()
