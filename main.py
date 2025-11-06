import os
import logging
import threading
import random

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

# ---------- ДАННЫЕ ДЛЯ ЗАДАНИЙ ----------

RESOURCES = [
    "любой луп из твоей библиотеки",
    "семпл голоса (можно свой)",
    "отрывок любимого трека (8 тактов)",
    "MIDI из старой сессии",
    "рандомный барабанный луп",
    "полевую запись/voice в телефоне",
    "звук, который был не для музыки (уведомление, кнопка, тиканье)",
]

TASKS = [
    "собери из этого 30–40 секунд трека",
    "сделай из этого драм-партию и накинь бас",
    "переверни звук (reverse) и используй как основу",
    "сделай 2 варианта: медленный и быстрый",
    "сделай интро, которое можно вставить в Reels",
    "нарежь и загруви — главное, чтобы качало",
    "сделай из этого пад/атмосферу и подложи ритм",
]

FOCUSES = [
    "фокус на драм-группе",
    "фокус на саунд-дизайне",
    "фокус на мелодии (простая, звуков 5–7)",
    "фокус на переходах между частями",
    "фокус на обработке (reverb/delay)",
    "фокус на басе",
    "фокус на структуре: интро → основа → аутро",
]

def generate_task() -> str:
    res = random.choice(RESOURCES)
    task = random.choice(TASKS)
    focus = random.choice(FOCUSES)

    return (
        "🎛 Музыкальное задание:\n\n"
        f"1. **Ресурс:** {res}\n"
        f"2. **Задание:** {task}\n"
        f"3. **Фокус:** {focus}\n\n"
        "Сохрани в дневник, когда сделаешь."
    )

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["🎲 Получить задание"],
        ["📚 Что это за система?"],
    ],
    resize_keyboard=True,
)

# ---------- ХЕНДЛЕРЫ ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот музыкальных заданий. Жми кнопку — я соберу тебе задание из трёх частей.",
        reply_markup=MAIN_KEYBOARD,
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()

    if "что это за система" in text:
        await update.message.reply_text(
            "Я собираю задания из трёх частей: ресурс → задание → фокус.\n"
            "• ресурс — из чего делать\n"
            "• задание — что именно сделать\n"
            "• фокус — на что обратить внимание при сведении/аранжировке\n\n"
            "Нажми «Получить задание» 👇",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    if "получить задание" in text:
        msg = generate_task()
        await update.message.reply_text(msg, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")
        return

    # всё остальное — просто поймали и дали задание
    msg = generate_task()
    await update.message.reply_text(msg, reply_markup=MAIN_KEYBOARD, parse_mode="Markdown")

# ---------- ЗАПУСК БОТА В ПОТОКЕ ----------

def run_telegram_bot():
    if not BOT_TOKEN:
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    # важно: в потоке сигналов быть не должно
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        stop_signals=None,
    )

# ---------- ENTRYPOINT ----------
if __name__ == "__main__":
    # бот в фоне
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # flask для render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
