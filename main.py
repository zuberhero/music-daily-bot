import os
import logging
import threading
import asyncio
import random

from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ==========================================================
# 1. Flask — чтобы Render видел живой сервис
# ==========================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Music Challenge Bot is alive!"


# ==========================================================
# 2. Логирование
# ==========================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ==========================================================
# 3. ENV
# ==========================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID_RAW = os.environ.get("CHANNEL_ID")  # формата -1001234567890

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else None
except ValueError:
    CHANNEL_ID = None
    logger.warning("⚠️ CHANNEL_ID задан неправильно — канал ловить не будем")

# тут храним последний пост из канала
LAST_CHANNEL_POST_KEY = "last_channel_post"


# ==========================================================
# 4. Данные для заданий (упрощённая «внутрянка»)
# ==========================================================
MIXING_TASKS = [
    "Сведи трек так, чтобы вокал/основной лид был тише, чем обычно. Проверь, что он всё равно читается.",
    "Сделай параллельную компрессию на барабаны и сравни с/без.",
    "Сделай sweep по частотам эквалайзером и вырежи всё, что реально бесит.",
]

MASTERING_TASKS = [
    "Возьми любой свой старый трек и сделай быстрый мастер: EQ → Comp → Limiter. Сравни с референсом.",
    "Сделай мастер так, чтобы LUFS был тише обычного, но ощущение плотности осталось.",
    "Сделай два мастера: один тёплый, другой яркий. Послушай в телефоне.",
]

SPACE_TASKS = [
    "Собери глубину: короткий реверб на ударные, длинный на пэды, дилей на лид.",
    "Сделай трек моно, а потом выведи только один элемент в стерео — должен стать заметным.",
    "Сделай слэп-дилей только на окончания фраз.",
]

BASS_TASKS = [
    "Настрой сайдчейн между киком и басом, но очень мягкий.",
    "Продублируй бас октавой выше и срежь всё ниже 200 Гц — для читаемости.",
    "Сделай бас не через компрессию, а через сатурацию и сравни.",
]

ALL_TASK_POOLS = MIXING_TASKS + MASTERING_TASKS + SPACE_TASKS + BASS_TASKS


# ==========================================================
# 5. Хендлеры команд
# ==========================================================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Привет! Это твой музыкальный бот 🎛\n\n"
        "Команды:\n"
        "/menu — что я умею\n"
        "/task — выдам рандомное задание\n"
        "/lucky — «мне повезёт» из всех пулов\n"
        "/paste — достану последний пост из канала-копилки\n"
        "/ghost — вернуть привидение 👻"
    )
    await update.message.reply_text(text)

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 Меню:\n"
        "• /task — музыкальное задание (сведение/мастеринг/пространство/бас)\n"
        "• /lucky — случайное задание из всех\n"
        "• /paste — последний пост из канала\n"
        "• /ghost — просто для настроения\n"
    )
    await update.message.reply_text(text)

async def ghost_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👻 бу. я здесь. не исчезаю. просто лежал в памяти.")

async def task_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # выбираем один из 4 пулов случайно
    pool = random.choice([MIXING_TASKS, MASTERING_TASKS, SPACE_TASKS, BASS_TASKS])
    task = random.choice(pool)
    await update.message.reply_text(f"🎯 Задание:\n{task}")

async def lucky_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # если вдруг список пустой — скажем честно
    if not ALL_TASK_POOLS:
        await update.message.reply_text("Пока не из чего выбирать 😔")
        return
    task = random.choice(ALL_TASK_POOLS)
    await update.message.reply_text(f"🍀 Мне повезёт:\n{task}")

async def paste_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.application.bot_data.get(LAST_CHANNEL_POST_KEY)
    if not data:
        await update.message.reply_text("Пока нет сохранённых постов из канала 😔")
        return
    await update.message.reply_text(data["text"], parse_mode="HTML")


# ==========================================================
# 6. Ловим посты из канала (через MessageHandler)
# ==========================================================
async def channel_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Тут мы ловим сообщения из каналов. Это вместо ChannelPostHandler,
    потому что твоя версия библиотеки его не знает.
    """
    if not CHANNEL_ID:
        return

    msg = update.effective_message
    if not msg:
        return

    # проверяем, что это именно тот канал
    if msg.chat.id != CHANNEL_ID:
        return

    text = msg.text_html or msg.caption_html or ""
    context.application.bot_data[LAST_CHANNEL_POST_KEY] = {
        "text": text,
        "has_media": bool(msg.photo or msg.video or msg.document),
    }
    logger.info("📥 Сохранили пост из канала: %s", text[:80])


# ==========================================================
# 7. Просто эхо на всякий случай (можно убрать)
# ==========================================================
async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Я тебя слышу, но у меня командами удобнее 📟 /menu")


# ==========================================================
# 8. Сборка приложения Telegram
# ==========================================================
def build_tg_app():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # команды
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("menu", menu_cmd))
    application.add_handler(CommandHandler("ghost", ghost_cmd))
    application.add_handler(CommandHandler("task", task_cmd))
    application.add_handler(CommandHandler("lucky", lucky_cmd))
    application.add_handler(CommandHandler("paste", paste_cmd))

    # канал
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_message_handler))

    # всё остальное — в эхо
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))

    return application


# ==========================================================
# 9. Запуск бота в отдельном потоке
# ==========================================================
def start_bot_in_thread(application):
    async def runner():
        # чтобы не было конфликтов со старым webhook
        await application.bot.delete_webhook(drop_pending_updates=True)
        # слушаем все типы апдейтов, чтобы канал точно пришёл
        await application.run_polling(allowed_updates=Update.ALL_TYPES)

    t = threading.Thread(target=lambda: asyncio.run(runner()), daemon=True)
    t.start()
    return t


# ==========================================================
# 10. Entry point
# ==========================================================
if __name__ == "__main__":
    tg_app = build_tg_app()
    start_bot_in_thread(tg_app)

    # Flask — без reloader, чтобы не поднялся второй процесс и не было 409
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
