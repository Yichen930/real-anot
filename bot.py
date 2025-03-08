import os
import requests
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re
import logging
import json
import urllib.parse
from flask import Flask, request

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("❌ Missing required environment variables!")

client = OpenAI(api_key=OPENAI_API_KEY)

# Trusted news sources
TRUSTED_SOURCES = [
    "bbc.com", "reuters.com", "apnews.com", "npr.org", "nytimes.com",
    "cnn.com", "washingtonpost.com", "forbes.com", "bloomberg.com",
    "theguardian.com", "aljazeera.com", "dw.com", "abc.net.au",
    "cbsnews.com", "nbcnews.com", "usatoday.com", "wsj.com", "latimes.com",
    "politico.com", "time.com", "newsweek.com", "pbs.org",
    "independent.co.uk", "telegraph.co.uk", "ft.com",
    "cbc.ca", "globalnews.ca", "ctvnews.ca",
    "smh.com.au", "theage.com.au", "abc.net.au",
    "france24.com", "euronews.com", "lemonde.fr", "spiegel.de", "derstandard.at",
    "straitstimes.com", "channelnewsasia.com",
    "thehindu.com", "indiatoday.in", "timesofindia.indiatimes.com",
    "bbc.com/mundo", "clarin.com", "eltiempo.com", "elpais.com",
    "africanews.com", "ewn.co.za", "mg.co.za",
    "scmp.com", "japantimes.co.jp", "koreatimes.co.kr"
]

# Fake news categories and meme responses
category_to_meme = {
    "Conspiracy Theory": "https://i.imgflip.com/1bij.jpg",
    "Fake Health News": "https://i.imgflip.com/26am.jpg",
    "AI-Generated Misinformation": "https://i.imgflip.com/4c1p.jpg",
    "Fake Science Claim": "https://i.imgflip.com/2h3r.jpg",
    "Political Misinformation": "https://i.imgflip.com/3w7cva.jpg",
    "Old News Reused": "https://i.imgflip.com/39t1o.jpg",
    "Clickbait & Fake News": "https://i.imgflip.com/30b1gx.jpg",
}

REPORTS_FILE = "reports.json"

# Check if the source URL is from a trusted news provider
def check_news_source(url):
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.replace("www.", "")
    return domain in TRUSTED_SOURCES

# Analyze news content using AI
async def check_fake_news_with_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Analyze the input and categorize it as one of the following:\n"
                                              "1. Conspiracy Theory\n"
                                              "2. Fake Health News\n"
                                              "3. AI-Generated Misinformation\n"
                                              "4. Fake Science Claim\n"
                                              "5. Political Misinformation\n"
                                              "6. Old News Reused\n"
                                              "7. Clickbait & Fake News\n"
                                              "If it does not fit any category, reply with: 'Not Fake News'."},
                {"role": "user", "content": text}
            ],
            temperature=0.7
        )

        category = response.choices[0].message.content.strip()

        if category in category_to_meme:
            return f"🧠 AI Analysis: This seems to be **{category}**.\n\nHere’s a meme to sum it up: {category_to_meme[category]}"

        return f"✅ No fake news detected.\n\n🧠 AI Analysis: {category}"

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return f"⚠️ Error retrieving AI analysis: {str(e)}"

# Detect fake news in messages
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    if len(text.split()) <= 10:
        ai_analysis = await check_fake_news_with_ai(text)
        await update.message.reply_text(ai_analysis)
        return

    ai_analysis = await check_fake_news_with_ai(text)
    await update.message.reply_text(f"🧠 AI Analysis:\n{ai_analysis}")

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

# Handle Telegram bot start command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the Fake News Meme Bot! 🤖\n"
        "Send me a message, and I'll check if it's fake news."
    )

# Error handling
async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"❌ Update {update} caused error {context.error}")

# Flask webhook for handling Telegram updates
flask_app = Flask(__name__)
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

@flask_app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), tg_app.bot)
    tg_app.process_update(update)
    return "OK"

# Start bot with Webhook
def start_webhook():
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    tg_app.add_handler(CommandHandler("report", report_false_positive))
    
    tg_app.bot.set_webhook(f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")

    flask_app.run(host="0.0.0.0", port=8443)

if __name__ == "__main__":
    start_webhook()
