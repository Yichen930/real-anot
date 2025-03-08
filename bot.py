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
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

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

REPORTS_FILE = "reports.json"

# Meme responses mapped to regex-detected categories
fake_news_keywords = {
    # 🔹 Conspiracy Theories
    r"\b(aliens?|UFO|extraterrestrial|area[\s-]?51|reptilian|illuminati|new[\s-]?world[\s-]?order|secret societies)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/2h3r.jpg", "⚠️ So… aliens are responsible for this too? 👽"),
    
    r"\b(government secret|deep[\s-]?state|hidden[\s-]?agenda|they don'?t want you to know|cover[\s-]?up|black[\s-]?ops|elites are controlling us|shadow government)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/4t0m5.jpg", "🚨 Ah yes, another 'they don’t want you to know this' moment. 😏"),

    # 🔹 Fake Health News
    r"\b(vaccines? (cause|lead to|are linked to) autism|anti[\s-]?vax|vaccine[\s-]?hoax|big[\s-]?pharma is lying|natural[\s-]?medicine is better than|essential oils cure everything|fluoride is dangerous|detox can remove toxins|miracle cure|doctors are lying|homeopathy works|covid vaccine is dangerous)\b": 
        ("Fake Health News", "https://i.imgflip.com/26am.jpg", "🧐 Oh, you have a PhD in WhatsApp Forwarding?"),

    # 🔹 AI-Generated Misinformation
    r"\b(this video proves|AI generated|deepfake|fake video|too realistic to be fake|manipulated[\s-]?media|synthetic[\s-]?content|robotic behavior|faked footage|fake interview|this video is 100% real|politician is a robot|robot president|not human)\b": 
        ("AI-Generated Misinformation", "https://i.imgflip.com/5z1hsc.jpg", "🤔 This looks AI-generated… because it is."),

    # 🔹 Fake Science Claims
    r"\b(quantum[\s-]?energy|frequencies|vibrations|5G is dangerous|radiation[\s-]?harm|electromagnetic[\s-]?weapon|waves affect the brain|phone signals cause cancer|scientists are hiding the truth|science is a lie|5G towers are harming people|microwave radiation|cell towers emit deadly radiation)\b": 
        ("Fake Science Claim", "https://i.imgflip.com/6ncocc.jpg", "🧠 This post used 'quantum' and 'frequencies,' so it must be legit?"),

    # 🔹 Political Misinformation
    r"\b(fake[\s-]?news|biased[\s-]?media|propaganda|mainstream[\s-]?media is lying|rigged[\s-]?election|false[\s-]?flag|election fraud|corrupt politicians|media blackout|cover-up by officials|votes were changed|ballots disappeared|illegal voting)\b": 
        ("Political Misinformation", "https://i.imgflip.com/3w7cva.jpg", "🤨 You sure this isn’t propaganda disguised as 'news'?"),

    # 🔹 Old News Reused
    r"\b(breaking[\s-]?news|shocking[\s-]?discovery|you won'?t believe|history[\s-]?rewritten|exposed after years|from [0-9]{4}|old report|10 years ago today|rediscovered|found after decades|this resurfaced|this happened years ago)\b": 
        ("Old News Reused", "https://i.imgflip.com/39t1o.jpg", "😂 BREAKING: This event happened… 10 years ago."),

    # 🔹 Clickbait & Fake News
    r"\b(scientists hate this|banned[\s-]?information|they don'?t want you to know|top[\s-]?secret[\s-]?files|hidden[\s-]?truth|wake up[\s-]?sheeple|shocking truth|forbidden knowledge|nobody is talking about this|click here to find out|you won'?t believe|secret discovery|massive coverup|mystery solved|revealed at last)\b": 
        ("Clickbait & Fake News", "https://i.imgflip.com/30b1gx.jpg", "😆 Clickbait title: 'Scientists HATE this simple trick!'"),
}

# Handle fake news detection
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, (category, meme_url, caption) in fake_news_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            await update.message.reply_photo(photo=meme_url, caption=f"🧠 **Category:** {category}\n\n{caption}")
            return

    await update.message.reply_text("✅ No fake news category detected.")

# Handle reporting of incorrect classifications
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
    await update.message.reply_text("Welcome to the Fake News Meme Bot! 🤖")

# Main function
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    app.add_handler(CommandHandler("report", report_false_positive))
    app.bot.set_webhook(f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")
    app.run_webhook(listen="0.0.0.0", port=8443, url_path=TELEGRAM_TOKEN, webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")

if __name__ == "__main__":
    main()
