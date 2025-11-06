import os
import logging
import threading
import asyncio

from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ChannelPostHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# 1. Flask, чтобы Render был счастлив
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Music Challenge Bot is alive!"


# =========================
# 2. Логирование
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# =========================
# 3. ENV
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID_RAW = os.environ.get("CHANNEL_ID")  # например -1001234567890

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else None
except ValueError:
    CHANNEL_ID = None
    logger.warning("⚠️ CHANNEL_ID задан неправильно, слушать канал не будем")

LAST_CHANNEL_POST_KEY = "last_channel_post"


# =========================
# 4. Хендлеры бота (базовые)
# =========================

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я на Render и я жив ✅")

async def ghost_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👻 музыкальный призрак на месте")

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ловим посты из твоего канала-копилки и кладём в память бота"""
    if not CHANNEL_ID:
        return

    post = update.channel_post
    if not post:
        return

    # проверяем, что это именно наш канал
    if post.chat.id != CHANNEL_ID:
        return

    text = post.text_html or post.caption_html or ""
    context.application.bot_data[LAST_CHANNEL_POST_KEY] = {
        "text": text,
        "has_media": bool(post.photo or post.video or post.document),
    }
    logger.info("📥 Сохранили пост из канала: %s", text[:80])

async def paste_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.application.bot_data.get(LAST_CHANNEL_POST_KEY)
    if not data:
        await update.message.reply_text("Пока нет сохранённых постов из канала 😔")
        return
    await update.message.reply_text(data["text"], parse_mode="HTML")


# =========================
# 5. ТВОЯ НАЧИНКА
# сюда вставь остальные хендлеры, которые у тебя были:
# меню, выдачу заданий, обработку команд и т.д.
# главное — добавь их потом в application в build_application()
# =========================

# пример: ловим любой текст
async def echo_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # это просто заглушка, можешь удалить
    await update.message.reply_text("Я получил: " + update.message.text)


# =========================
# 6. Сборка приложения
# =========================
def build_application() -> "ApplicationBuilder":
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # базовые команды
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("ghost", ghost_cmd))
    application.add_handler(CommandHandler("paste", paste_cmd))

    # канал
    application.add_handler(ChannelPostHandler(channel_post_handler))

    # твои прочие хендлеры сюда:
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_text))

    return application


# =========================
# 7. Запуск бота в отдельном потоке
# =========================
def start_bot_thread(application):
    async def runner():
        # на всякий случай: если когда-то стоял webhook — убьём
        await application.bot.delete_webhook(drop_pending_updates=True)
        # слушаем ВСЁ, чтобы ловить channel_post
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    t = threading.Thread(target=lambda: asyncio.run(runner()), daemon=True)
    t.start()
    return t


# =========================
# 8. Entry point
# =========================
if __name__ == "__main__":
    # 1) собираем приложение телеграма
    application = build_application()

    # 2) запускаем бота в отдельном потоке
    start_bot_thread(application)

    # 3) запускаем Flask БЕЗ reloader, чтобы не было второго процесса
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
