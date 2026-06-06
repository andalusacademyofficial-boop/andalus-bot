import os
import logging
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

CHOOSING, ASKING = range(2)

SUBJECTS = {
    "1 اساسيات التمريض": "اساسيات التمريض والمصطلحات الطبية",
    "2 الاسعافات الاولية": "الاسعافات الاولية",
    "3 التغذية العلاجية": "التغذية العلاجية",
    "4 العناية المركزة": "العناية المركزة",
    "5 التمريض الباطني": "التمريض الباطني والطوارئ",
    "6 تمريض النسا والتوليد": "تمريض النسا والتوليد",
    "7 مكافحة العدوى": "مكافحة العدوى",
}

MATERIALS = {}

def load_materials():
    folder = "materials"
    if not os.path.exists(folder):
        return
    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            subject = filename.replace(".txt", "")
            with open(f"{folder}/{filename}", "r", encoding="utf-8") as f:
                MATERIALS[subject] = f.read()
    logging.info(f"مواد محملة: {list(MATERIALS.keys())}")

async def start(update, context):
    keyboard = [[k] for k in SUBJECTS.keys()]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("اهلا بك في بوت مركز الاندلس\n\nاختار المادة:", reply_markup=markup)
    return CHOOSING

async def choose_subject(update, context):
    chosen = update.message.text
    if chosen not in SUBJECTS:
        await update.message.reply_text("اختار من القايمة بس")
        return CHOOSING
    context.user_data["subject"] = SUBJECTS[chosen]
    await update.message.reply_text(f"اخترت: {SUBJECTS[chosen]}\n\nاسأل سؤالك:", reply_markup=ReplyKeyboardRemove())
    return ASKING

async def answer_question(update, context):
    question = update.message.text
    subject = context.user_data.get("subject", "")

    if question == "ارجع للمواد":
        return await start(update, context)

    await update.message.reply_text("بفكر...")

    material = MATERIALS.get(subject, "مفيش محتوى لهذه المادة")
    logging.info(f"المادة: {subject} - المواد المتاحة: {list(MATERIALS.keys())}")

    try:
        m = genai.GenerativeModel("gemini-1.5-flash")
        prompt = "انت مساعد تعليمي. المادة: " + subject + "\nالمنهج:\n" + material[:10000] + "\n\nسؤال الطالب: " + question + "\n\nاجب بالعربي بشكل مبسط."
        response = m.generate_content(prompt)
        answer = response.text
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        answer = f"خطأ: {str(e)}"

    markup = ReplyKeyboardMarkup([["ارجع للمواد"]], resize_keyboard=True)
    await update.message.reply_text(answer, reply_markup=markup)
    return ASKING

def main():
    load_materials()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_subject)],
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    app.add_handler(conv)
    logging.info("البوت شغال")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
