import os
import json
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

TOKEN       = os.getenv("BOT_TOKEN")
ADMIN_TG_ID = 8444937478          # твой ID
USERS_FILE  = "users.json"

# ➜ ловим send_to: 'AW-<id>/<label>'
PATTERN = re.compile(r"send_to\s*:\s*['\"]?(?:AW-)?(\d+)/([^'\"\s,}]+)['\"]?")

# ---------- учёт ----------
def load_users() -> set:
    if os.path.isfile(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_users(users: set) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users), f, ensure_ascii=False)

async def track_user(user_id: int, username: str | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        save_users(users)
        await context.bot.send_message(
            chat_id=ADMIN_TG_ID,
            text=f"Новый пользователь: @{username or 'без_username'} ({user_id}) → всего {len(users)} человек"
        )

# ---------- команды ----------
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    total = len(load_users())
    await update.message.reply_text(f"📊 Всего уникальных пользователей: {total}")

# ---------- основная логика ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await track_user(user.id, user.username, context)

    text   = update.message.text or ""
    matches = PATTERN.findall(text)
    if not matches:
        await update.message.reply_text("❌ Не найдено подходящих gtag conversion событий.")
        return

    counts   = Counter(matches)
    unique   = list(counts)
    lines    = [f"/?aw={aw_id}&awc={awc}" for aw_id, awc in unique]
    result   = "\n".join(lines)

    duplicates = {k: v for k, v in counts.items() if v > 1}
    warn_lines = [
        f"⚠️  дубль – /?aw={aw_id}&awc={awc}, встречается {cnt} раз"
        for (aw_id, awc), cnt in duplicates.items()
    ]
    warn_text = "\n".join(warn_lines) + "\n\n" if warn_lines else ""

    keyboard = [[InlineKeyboardButton("📋 Скопировать всё", callback_data="copy")]]
    await update.message.reply_text(
        f"{warn_text}✅ Готово:\n\n<pre>{result}</pre>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
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

# ---------- запуск ----------
def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^copy$"))
    app.run_polling()

if __name__ == "__main__":
    main()
