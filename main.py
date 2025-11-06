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

# ---------- Твои хендлеры ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Жми кнопку и работай ✨")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower()

    if "система" in text:
        await update.message.reply_text(
            "Я собираю задания из трёх частей: ресурс → задание → фокус.\n"
            "Жми кнопку и работай."
        )
    else:
        # тут будет твоя логика музыкальных заданий
        await update.message.reply_text("Поймала сообщение, готовлю муз-задание 🎛")

def run_telegram_bot():
    """Запускает Telegram-бота в этом потоке, без лишнего asyncio."""
    if not BOT_TOKEN:
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # run_polling сам удаляет webhook и блокирует поток
    application.run_polling(allowed_updates=Update.ALL_TYPES)

# ---------- Точка входа ----------
if __name__ == "__main__":
    # запускаем бота в фоне
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # запускаем Flask для Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
