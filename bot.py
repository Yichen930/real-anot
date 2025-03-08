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
OPENAI_API_URL = os.getenv("OPENAI_API_URL")  # Your custom API URL
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not OPENAI_API_URL or not WEBHOOK_URL:
    raise ValueError("❌ Missing required environment variables!")

client = OpenAI(base_url=OPENAI_API_URL, api_key=OPENAI_API_KEY)

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

# Faster regex-based meme detection
fake_news_keywords = {
    r"\b(aliens?|UFO|extraterrestrial|area[\s-]?51|reptilian|illuminati|new[\s-]?world[\s-]?order)\b": "https://i.imgflip.com/1bij.jpg",
    r"\b(government secret|deep[\s-]?state|hidden[\s-]?agenda|they don'?t want you to know|cover[\s-]?up|black[\s-]?ops)\b": "https://i.imgflip.com/4t0m5.jpg",
    r"\b(trust me, I'?m a doctor|miracle cure|big[\s-]?pharma|natural[\s-]?medicine|homeopathy|detox|superfood|cancer[\s-]?cure)\b": "https://i.imgflip.com/26am.jpg",
    r"\b(I did my own research|essential oils|herbal remedy|anti[\s-]?vax|vaccine[\s-]?hoax|fluoride is dangerous)\b": "https://i.imgflip.com/5g9o3h.jpg",
    r"\b(deepfake|AI generated|fake video|too realistic|manipulated[\s-]?media|synthetic[\s-]?content)\b": "https://i.imgflip.com/4c1p.jpg",
    r"\b(quantum[\s-]?energy|frequencies|vibrations|5G is dangerous|radiation[\s-]?harm|electromagnetic[\s-]?weapon)\b": "https://i.imgflip.com/2h3r.jpg",
    r"\b(fake[\s-]?news|biased[\s-]?media|propaganda|mainstream[\s-]?media is lying|rigged[\s-]?election|false[\s-]?flag)\b": "https://i.imgflip.com/3w7cva.jpg",
    r"\b(breaking[\s-]?news|shocking[\s-]?discovery|you won'?t believe|history[\s-]?rewritten|exposed after years)\b": "https://i.imgflip.com/39t1o.jpg",
    r"\b(scientists hate this|banned[\s-]?information|they don'?t want you to know|top[\s-]?secret[\s-]?files|hidden[\s-]?truth|wake up[\s-]?sheeple)\b": "https://i.imgflip.com/30b1gx.jpg",
}

# Check if the source URL is from a trusted news provider
def check_news_source(url):
    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc.replace("www.", "")
    return domain in TRUSTED_SOURCES

# AI-assisted fake news analysis
async def check_fake_news_with_ai(text):
    try:
        response = requests.post(
            OPENAI_API_URL,
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "messages": [{"role": "user", "content": f"Is this misinformation? {text}"}]}
        )
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "⚠️ AI could not analyze this.")
    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return "⚠️ Error retrieving AI analysis."

# Detect fake news using regex (fast) + AI analysis
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, meme_url in fake_news_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            ai_analysis = await check_fake_news_with_ai(text)
            await update.message.reply_photo(photo=meme_url, caption=f"🧠 AI Analysis:\n{ai_analysis}")
            return

    ai_analysis = await check_fake_news_with_ai(text)
    await update.message.reply_text(f"🧠 AI Analysis:\n{ai_analysis}")

# Telegram `/start` command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to the Fake News Meme Bot! 🤖 Send me a message, and I'll check if it's fake news.")

# Webhook for Telegram bot updates
flask_app = Flask(__name__)
tg_app = Application.builder().token(TELEGRAM_TOKEN).build()

@flask_app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(), tg_app.bot)
    await tg_app.process_update(update)  # Fixed asyncio warning
    return "OK"

# Start Webhook
def start_webhook():
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))

    tg_app.bot.set_webhook(f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}")

    flask_app.run(host="0.0.0.0", port=8443)

if __name__ == "__main__":
    start_webhook()
