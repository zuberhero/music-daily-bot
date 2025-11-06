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

# --- Flask-сервер для Render ---
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Music Challenge Bot is alive!"

# --- Telegram-бот ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

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
    "Сделай 8 секунд звука, которые тебе нравятся. Или 16, если идёт хорошо.",
    "Сдвинь кик или снейр на пару миллисекунд — найди, где начинается кач.",
]

FOCUSES = [
    "Ограничение по времени: 15 минут.",
    "Только встроенные плагины.",
    "Без ударных.",
    "Только шумы и записи реального мира.",
    "Пусть всё звучит как утро.",
]

MAIN_KB =_
