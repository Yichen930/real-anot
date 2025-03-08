import os
import requests
import logging
import json
import asyncio
import re
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Load environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Debugging: Check missing environment variables
missing_vars = []
if not TELEGRAM_TOKEN: missing_vars.append("TELEGRAM_BOT_TOKEN")
if not OPENAI_API_KEY: missing_vars.append("OPENAI_API_KEY")
if not WEBHOOK_URL: missing_vars.append("WEBHOOK_URL")

if missing_vars:
    raise ValueError(f"❌ Missing required environment variables: {', '.join(missing_vars)}")

client = OpenAI(api_key=OPENAI_API_KEY)

# Meme responses mapped to regex-detected categories
fake_news_keywords = {
    # 🔹 Conspiracy Theories
    r"\b(aliens?|UFO|extraterrestrial|area[\s-]?51|reptilian|illuminati|new[\s-]?world[\s-]?order)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/1bij.jpg"),
    r"\b(government secret|deep[\s-]?state|hidden[\s-]?agenda|they don'?t want you to know|cover[\s-]?up|black[\s-]?ops)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/4t0m5.jpg"),

    # 🔹 Fake Health News (Expanded for better detection)
    r"\b(vaccines? (cause|lead to|are linked to) autism|anti[\s-]?vax|vaccine[\s-]?hoax|big[\s-]?pharma is lying|natural[\s-]?medicine is better than|essential oils cure everything|fluoride is dangerous|detox can remove toxins)\b": 
        ("Fake Health News", "https://i.imgflip.com/26am.jpg"),
    r"\b(trust me, I'?m a doctor|miracle cure|homeopathy works|doctors are lying|big pharma doesn'?t want you to know)\b": 
        ("Fake Health News", "https://i.imgflip.com/5g9o3h.jpg"),

    # 🔹 AI-Generated Misinformation
    r"\b(deepfake|AI generated|fake video|too realistic|manipulated[\s-]?media|synthetic[\s-]?content)\b": 
        ("AI-Generated Misinformation", "https://i.imgflip.com/4c1p.jpg"),

    # 🔹 Fake Science Claims
    r"\b(quantum[\s-]?energy|frequencies|vibrations|5G is dangerous|radiation[\s-]?harm|electromagnetic[\s-]?weapon)\b": 
        ("Fake Science Claim", "https://i.imgflip.com/2h3r.jpg"),

    # 🔹 Political Misinformation
    r"\b(fake[\s-]?news|biased[\s-]?media|propaganda|mainstream[\s-]?media is lying|rigged[\s-]?election|false[\s-]?flag)\b": 
        ("Political Misinformation", "https://i.imgflip.com/3w7cva.jpg"),

    # 🔹 Old News Reused
    r"\b(breaking[\s-]?news|shocking[\s-]?discovery|you won'?t believe|history[\s-]?rewritten|exposed after years)\b": 
        ("Old News Reused", "https://i.imgflip.com/39t1o.jpg"),

    # 🔹 Clickbait & Fake News
    r"\b(scientists hate this|banned[\s-]?information|they don'?t want you to know|top[\s-]?secret[\s-]?files|hidden[\s-]?truth|wake up[\s-]?sheeple)\b": 
        ("Clickbait & Fake News", "https://i.imgflip.com/30b1gx.jpg"),
}


REPORTS_FILE = "reports.json"

# AI analyzes the text but does not pick the category
async def analyze_news_with_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                    "You are a fact-checking assistant. "
                    "Analyze the following text and provide a brief analysis of whether it contains misinformation or exaggerations."
                    "Do NOT categorize it—just provide a factual analysis."},
                {"role": "user", "content": text}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return "⚠️ Error retrieving AI analysis."

# Detect fake news using regex + AI analysis
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, (category, meme_url) in fake_news_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            ai_analysis = await analyze_news_with_ai(text)
            await update.message.reply_photo(photo=meme_url, caption=f"🧠 **Category:** {category}\n\n{ai_analysis}")
            return

    ai_analysis = await analyze_news_with_ai(text)
    await update.message.reply_text(f"✅ No fake news category detected.\n\n🧠 AI Analysis:\n{ai_analysis}")

# Allow users to report misclassifications
async def report_false_positive(update: Update, context: CallbackContext) -> None:
    user_text = " ".join(context.args)
    
    if not user_text:
        await update.message.reply_text("⚠️ Please provide the misclassified statement. Example:\n/report The government is hiding UFOs!")
        return

    try:
        with open(REPORTS_FILE, "r") as file:
            reports = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        reports = []

    reports.append(user_text)
    
    with open(REPORTS_FILE, "w") as file:
        json.dump(reports, file, indent=4)

    await update.message.reply_text("✅ Thank you! Your report has been logged.")

# Telegram `/start` command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the Fake News Meme Bot! 🤖\n"
        "Send me a message, and I'll check if it's fake news.\n"
        "Use /report <message> if you find an incorrect classification."
    )

# Main function (runs webhook server without Flask)
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    app.add_handler(CommandHandler("report", report_false_positive))

    # Set Webhook
    app.bot.set_webhook(f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")

    # Run webhook server
    app.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
