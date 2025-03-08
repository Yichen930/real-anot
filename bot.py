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

# Meme responses mapped to regex-detected categories (Updated with working URLs)
fake_news_keywords = {
    r"\b(aliens?|UFO|extraterrestrial|area[\s-]?51|reptilian|illuminati|new[\s-]?world[\s-]?order|secret societies)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/2h3r.jpg"),

    r"\b(government secret|deep[\s-]?state|hidden[\s-]?agenda|they don'?t want you to know|cover[\s-]?up|black[\s-]?ops|elites are controlling us|shadow government)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/4t0m5.jpg"),

    r"\b(vaccines? (cause|lead to|are linked to) autism|anti[\s-]?vax|vaccine[\s-]?hoax|big[\s-]?pharma is lying|natural[\s-]?medicine is better than|essential oils cure everything|fluoride is dangerous|detox can remove toxins|miracle cure|doctors are lying|homeopathy works|covid vaccine is dangerous)\b": 
        ("Fake Health News", "https://i.imgflip.com/26am.jpg"),

    r"\b(this video proves|AI generated|deepfake|fake video|too realistic to be fake|manipulated[\s-]?media|synthetic[\s-]?content|robotic behavior|faked footage|fake interview|this video is 100% real|politician is a robot|robot president|not human)\b": 
        ("AI-Generated Misinformation", "https://i.imgflip.com/5z1hsc.jpg"),

    r"\b(quantum[\s-]?energy|frequencies|vibrations|5G is dangerous|radiation[\s-]?harm|electromagnetic[\s-]?weapon|waves affect the brain|phone signals cause cancer|scientists are hiding the truth|science is a lie|5G towers are harming people|microwave radiation|cell towers emit deadly radiation)\b": 
        ("Fake Science Claim", "https://i.imgflip.com/6ncocc.jpg"),

    r"\b(fake[\s-]?news|biased[\s-]?media|propaganda|mainstream[\s-]?media is lying|rigged[\s-]?election|false[\s-]?flag|election fraud|corrupt politicians|media blackout|cover-up by officials|votes were changed|ballots disappeared|illegal voting)\b": 
        ("Political Misinformation", "https://i.imgflip.com/3w7cva.jpg"),

    r"\b(breaking[\s-]?news|shocking[\s-]?discovery|you won'?t believe|history[\s-]?rewritten|exposed after years|from [0-9]{4}|old report|10 years ago today|rediscovered|found after decades|this resurfaced|this happened years ago)\b": 
        ("Old News Reused", "https://i.imgflip.com/39t1o.jpg"),

    r"\b(scientists hate this|banned[\s-]?information|they don'?t want you to know|top[\s-]?secret[\s-]?files|hidden[\s-]?truth|wake up[\s-]?sheeple|shocking truth|forbidden knowledge|nobody is talking about this|click here to find out|you won'?t believe|secret discovery|massive coverup|mystery solved|revealed at last)\b": 
        ("Clickbait & Fake News", "https://i.imgflip.com/30b1gx.jpg"),
}

# Detect fake news using regex + AI analysis
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, (category, meme_url) in fake_news_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            try:
                await update.message.reply_photo(photo=meme_url, caption=f"🧠 **Category:** {category}")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Error sending meme. **Category:** {category}")
                logging.error(f"Error sending meme for '{text}': {e}")

            return

    await update.message.reply_text("✅ No fake news category detected.")

# Error handling
async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"Update {update} caused error {context.error}")

# Telegram `/start` command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the Fake News Meme Bot! 🤖\n"
        "Send me a message, and I'll check if it's fake news."
    )

# Main function (runs webhook server without Flask)
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    app.add_error_handler(error_handler)

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
