import os
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Settings
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    for filename in os.listdir("materials"):
        if filename.endswith(".txt"):
            subject = filename.replace(".txt", "")
            with open(f"materials/{filename}", "r", encoding="utf-8") as f:
                MATERIALS[subject] = f.read()

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
    )
    return ASKING

async def answer_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    subject = context.user_data.get("subject")
    material = MATERIALS.get(subject, "")

    if question == "🔙 ارجع للمواد":
        return await start(update, context)

    await update.message.reply_text("⏳ بفكر...")

    prompt = f"""أنت مساعد تعليمي متخصص في مركز الاندلس للتدريب.
المادة: {subject}
محتوى المنهج:
{material[:15000]}

سؤال الطالب: {question}

أجب بالعربي بشكل واضح ومبسط من المنهج فقط. لو السؤال مش موجود في المنهج قول للطالب بأدب."""

    try:
        response = model.generate_content(prompt)
        answer = response.text
    except Exception as e:
        answer = "حصل خطأ، حاول تاني بعد شوية."

    keyboard = [["🔙 ارجع للمواد"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(answer, reply_markup=reply_markup)
    return ASKING

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)

def main():
    load_materials()
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_subject)],
            ASKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app.add_handler(conv_handler)
    print("البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
