import os
import re
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
Application,
@@ -22,20 +23,37 @@ async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) ->
if not matches:
await update.message.reply_text("❌ Не найдено подходящих gtag conversion событий.")
return
    unique = list(dict.fromkeys(matches))

    # подсчёт повторов
    counts = Counter(matches)
    duplicates = {k: v for k, v in counts.items() if v > 1}

    # формируем уникальные строки для вывода
    unique = list(counts)          # порядок сохраняется
lines = [f"/?aw={aw_id}&awc={awc}" for aw_id, awc in unique]
result = "\n".join(lines)

    # собираем предупреждения о дублях
    warn_lines = []
    for (aw_id, awc), cnt in duplicates.items():
        warn_lines.append(
            f"⚠️  дубль – /?aw={aw_id}&awc={awc}, встречается {cnt} раз"
        )
    warn_text = "\n".join(warn_lines) + "\n\n" if warn_lines else ""

keyboard = [[InlineKeyboardButton("📋 Скопировать всё", callback_data="copy")]]
await update.message.reply_text(
        f"✅ Готово:\n\n<pre>{result}</pre>",
        f"{warn_text}✅ Готово:\n\n<pre>{result}</pre>",
parse_mode="HTML",
reply_markup=InlineKeyboardMarkup(keyboard),
)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
query = update.callback_query
await query.answer()
    clean = query.message.text.replace("✅ Готово:\n\n<pre>", "").replace("</pre>", "")
    # убираем служебный префикс и теги
    clean = query.message.text
    clean = clean.split("✅ Готово:\n\n<pre>")[-1].replace("</pre>", "")
await query.message.reply_text(f"📋 Для копирования:\n\n{clean}")

def main() -> None:


проверь этот код, почему он не работает корректно, постоянно приходит письмо с github что отменен запуск
