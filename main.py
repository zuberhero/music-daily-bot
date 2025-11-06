import os
import random
import logging
import asyncio
from flask import Flask
from telegram import ReplyKeyboardMarkup, Update
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

# ---------- Данные для генерации ----------
RESOURCES = [
    "Pinterest: возьми гайд или аккорды (https://pin.it/5mY6kTJlH)",
    "Reels: открой сохранёнку с референсом и возьми идею оттуда",
    "Старые проекты: открой незаконченный проект и используй один элемент",
    "Книга «Твой первый трек»: выбери главу под навык (ритм, гармония, звук)",
    "Случайный звук: запиши бытовой шум/голос/поле и используй как исходник",
]

ACTIONS = [
    "Сделай что-то нарочно некрасивое, просто чтобы разогреться.",
    "Повтори ритм, который слышишь вокруг.",
    "Возьми луп из старого трека, оставь одну дорожку и построй вокруг неё новое.",
    "Сделай 8 секунд звука, которые тебе нравятся. Если идёт хорошо, сделай 16 или 32.",
    "Сдвинь кик или снейр на пару миллисекунд и найди, где начинается кач.",
    "Сделай ритм, где каждый удар отличается (громкость/пэн/длина).",
    "Сделай минутный трек, где каждые 4 такта что-то меняется.",
]

FOCUSES = [
    "Ограничение по времени: 15 минут.",
    "Только встроенные плагины.",
    "Без ударных.",
    "Только шумы и записи реального мира.",
    "Пусть всё звучит как утро.",
]

MAIN_KB = ReplyKeyboardMarkup(
    [["🎲 Получить задание"], ["📚 Что это за система?"]],
    resize_keyboard=True,
)

# ---------- Логика генерации ----------
def build_task() -> str:
    resource = random.choice(RESOURCES)
    action = random.choice(ACTIONS)
    focus = random.choice(FOCUSES)
    return (
        f"РЕСУРС:\n• {resource}\n\n"
        f"ЗАДАНИЕ:\n• {action}\n\n"
        f"ФОКУС:\n• {focus}"
    )

# ---------- Хендлеры бота ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет. Я твой музыкальный пинок.\nЖми «🎲 Получить задание».",
        reply_markup=MAIN_KB,
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower()
    if "получить" in text:
        await update.message.reply_text(build_task(), reply_markup=MAIN_KB)
    elif "система" in text:
        await update.message.reply_text(
            "Я собираю задачу из трёх частей: ресурс → задание → фокус.\n"
            "Ты жми кнопку и работай.",
            reply_markup=MAIN_KB,
        )
    else:
        await update.message.reply_text(
            "Жми кнопку. Не усложняй.",
            reply_markup=MAIN_KB,
        )

# ---------- Запуск бота ----------
async def run_bot():
    token = BOT_TOKEN
    if not token:
        raise RuntimeError("Нет BOT_TOKEN в переменных окружения")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Бот запущен. Иди в Telegram.")
    await application.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    # Flask держит веб-сервис для Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
