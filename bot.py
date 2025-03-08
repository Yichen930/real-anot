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
}

# 🔹 Function to Check with Custom AI API
async def check_fake_news_with_api(text):
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",  
            "messages": [{"role": "user", "content": f"Is the following statement misinformation? Provide a short explanation:\n{text}"}]
        }

        response = requests.post(OPENAI_API_URL, json=payload, headers=headers)
        response_json = response.json()

        if "choices" in response_json and response_json["choices"]:
            return response_json["choices"][0]["message"]["content"]
        else:
            return "⚠️ AI analysis failed. The response was unexpected."

    except Exception as e:
        logging.error(f"Custom API error: {e}")
        return "⚠️ Error retrieving AI analysis."

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
