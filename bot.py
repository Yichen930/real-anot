import os
import requests
import logging
import json
import asyncio
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

# Meme responses mapped to AI-detected categories
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

# AI categorizes news into fake news types
async def categorize_news_with_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                    "You are an expert fact-checker. "
                    "Your job is to analyze the input and strictly classify it into one of these categories:\n"
                    "1. Conspiracy Theory\n"
                    "2. Fake Health News\n"
                    "3. AI-Generated Misinformation\n"
                    "4. Fake Science Claim\n"
                    "5. Political Misinformation\n"
                    "6. Old News Reused\n"
                    "7. Clickbait & Fake News\n"
                    "If it is real news or factual, reply with: 'Not Fake News'.\n"
                    "Do NOT say 'Not Fake News' unless you are 100% sure the statement is factual and backed by evidence."},
                {"role": "user", "content": text}
            ],
            temperature=0.3  # Lower temperature for more consistent responses
        )

        category = response.choices[0].message.content.strip()

        if category in category_to_meme:
            return category, category_to_meme[category]

        return "Not Fake News", ""

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return "Error analyzing news", ""

# Detect fake news and send meme if applicable
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()
    
    category, meme_url = await categorize_news_with_ai(text)
    
    if category != "Not Fake News" and meme_url:
        await update.message.reply_photo(photo=meme_url, caption=f"🧠 AI Analysis: This seems to be **{category}**.")
    else:
        await update.message.reply_text(f"✅ No fake news detected.\n\n🧠 AI Analysis: {category}")

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
