import os
import logging
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

CHOOSING, ASKING = range(2)

SUBJECTS = {
    "1️⃣ اساسيات التمريض والمصطلحات الطبية": "اساسيات التمريض والمصطلحات الطبية",
    "2️⃣ الاسعافات الاولية": "الاسعافات الاولية",
    "3️⃣ التغذية العلاجية": "التغذية العلاجية",
    "4️⃣ العناية المركزة": "العناية المركزة",
    "5️⃣ التمريض الباطني والطوارئ": "التمريض الباطني والطوارئ",
    "6️⃣ تمريض النسا والتوليد": "تمريض النسا والتوليد",
    "7️⃣ مكافحة العدوى": "مكافحة العدوى",
}

MATERIALS = {}

def load_materials():
    folder = "materials"
    if not os.path.exists(folder):
        logging.warning("فولدر materials مش موجود")
        return
    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            subject = filename.replace(".txt", "")
            with open(f"{folder}/{filename}", "r", encoding="utf-8") as f:
                MATERIALS[subject] = f.read()
    logging.info(f"تم تحميل {len(MATERIALS)} مادة: {list(MATERIALS.keys())}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[key] for key in SUBJECTS.keys()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "👋 أهلاً بك في بوت مركز الاندلس للتدريب!\n\nاختار المادة اللي عاوز تسأل فيها:",
        reply_markup=reply_markup
    )
    return CHOOSING

async def choose_subject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen = update.message.text
    if chosen not in SUBJECTS:
        await update.message.reply_text("اختار من القايمة بس ✋")
        return CHOOSING
    context.user_data["subject"] = SUBJECTS[chosen]
    await update.message.reply_text(
        f"✅ اخترت: {SUBJECTS[chosen]}\n\nاتفضل اسأل سؤالك:",
        reply_markup=ReplyKeyboardRemove()
