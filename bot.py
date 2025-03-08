import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re
import logging

# 🔹 Enable Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# 🔹 Get API Credentials from Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_URL = os.getenv("OPENAI_API_URL")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Webhook URL for deployment

# Ensure API credentials exist
if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")
if not OPENAI_API_KEY or not OPENAI_API_URL:
    raise ValueError("Missing OPENAI_API_KEY or OPENAI_API_URL environment variable!")

# 🔹 Define Fake News Keywords and Responses (Verified Meme Links)
fake_news_keywords = {
    # 1️⃣ Conspiracy Theories
    r"aliens|UFO|extraterrestrial": {
        "text": "⚠️ So… aliens are responsible for this too? 👽",
        "meme": "https://i.imgflip.com/1bij.jpg"
    },
    r"government secret|hiding something|deep state|they don’t want you to know": {
        "text": "🚨 Ah yes, another 'they don’t want you to know this' moment. 😏",
        "meme": "https://i.imgflip.com/4t0m5.jpg"
    },

    # 2️⃣ Fake Health News
    r"trust me, I’m a doctor|miracle cure|big pharma is lying": {
        "text": "🧐 Oh, you have a PhD in WhatsApp Forwarding?",
        "meme": "https://i.imgflip.com/26am.jpg"
    },
    r"I did my own research|natural remedies|essential oils cure everything": {
        "text": "🔬 And by research, you mean watching a YouTube video?",
        "meme": "https://i.imgflip.com/5g9o3h.jpg"
    },

    # 3️⃣ Deepfake & AI-Generated Misinformation
    r"AI generated|deepfake|fake video|too realistic": {
        "text": "🤔 This looks AI-generated… because it is.",
        "meme": "https://i.imgflip.com/4c1p.jpg"
    },

    # 4️⃣ Fake Science Claims
    r"quantum energy|frequencies|5G is dangerous": {
        "text": "🧠 This post used 'quantum' and 'frequencies,' so it must be legit?",
        "meme": "https://i.imgflip.com/2h3r.jpg"
    },

    # 5️⃣ Political Misinformation
    r"fake news|biased media|propaganda|mainstream media is lying": {
        "text": "🤨 You sure this isn’t propaganda disguised as 'news'?",
        "meme": "https://i.imgflip.com/3w7cva.jpg"
    },

    # 6️⃣ Old News Used As New
    r"breaking news|shocking discovery|you won’t believe": {
        "text": "😂 BREAKING: This event happened… 10 years ago.",
        "meme": "https://i.imgflip.com/39t1o.jpg"
    },

    # 7️⃣ Clickbait & Fake News
    r"scientists hate this|banned information|they don’t want you to know": {
        "text": "😆 Clickbait title: 'Scientists HATE this simple trick!'",
        "meme": "https://i.imgflip.com/30b1gx.jpg"
    },
}

from openai import OpenAI  # ✅ 使用 OpenAI SDK

# 🔹 初始化 OpenAI 客户端
client = OpenAI(
    base_url=os.getenv("OPENAI_API_URL", "https://chatapi.littlewheat.com/v1"),  # ✅ 默认正确路径
    api_key=os.getenv("OPENAI_API_KEY")
)

async def check_fake_news_with_api(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[{"role": "user", "content": f"Is this misinformation? {text}"}],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Custom API error: {e}")
        return f"⚠️ Error retrieving AI analysis: {str(e)}"


# 🔹 Function to Detect Fake News and Get AI Feedback
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, response in fake_news_keywords.items():
        if re.search(pattern, text):
            ai_analysis = await check_fake_news_with_api(text)
            try:
                await update.message.reply_photo(
                    photo=response["meme"], 
                    caption=f"{response['text']}\n\n🧠 AI Analysis:\n{ai_analysis}"
                )
            except Exception as e:
                await update.message.reply_text(f"{response['text']}\n\n🧠 AI Analysis:\n{ai_analysis}")
                logging.error(f"Error sending meme for '{text}': {e}")
            return

    ai_analysis = await check_fake_news_with_api(text)
    await update.message.reply_text(f"🧠 AI Analysis:\n{ai_analysis}")

# 🔹 Start Command
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the Fake News Meme Bot! 🤖\n"
        "Send me a message, and I'll check if it's fake news."
    )

# 🔹 Error Handling
async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"Update {update} caused error {context.error}")

# 🔹 Main Function (Webhooks Version)
def main():
    # ✅ Correctly Define `app` Before Webhooks
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    app.add_error_handler(error_handler)

    # ✅ Use Webhooks Instead of Polling
    app.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path=TELEGRAM_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
    )

if __name__ == "__main__":
    main()
