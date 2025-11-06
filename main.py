import os
import logging
import threading

from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------- Flask для Render ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Music Challenge Bot is alive!"

# ---------- Логирование ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не задан в переменных окружения!")

# ---------- твои хендлеры ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # сюда потом вернём твою “собираю задание из трёх частей”
    await update.message.reply_text("Привет! Я жив. Жми кнопку и работай 🎛")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower()

    if "система" in text:
        await update.message.reply_text(
            "Я собираю задания из трёх частей: ресурс → задание → фокус.\n"
            "Жми кнопку и работай."
        )
    else:
        await update.message.reply_text("Приняла. Могу сгенерить муз-задание 🎶")

def run_telegram_bot():
    """Запуск бота в отдельном потоке БЕЗ сигналов."""
    if not BOT_TOKEN:
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # КЛЮЧ: stop_signals=None — чтобы не падать в потоке
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        stop_signals=None,
    )

if __name__ == "__main__":
    # запускаем бота в фоне
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # запускаем Flask — это нужно Render’у
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
