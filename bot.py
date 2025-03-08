import os
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re
import logging

# 🔹 Enable Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# 🔹 Get Tokens from Environment Variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure tokens exist
if not TELEGRAM_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable!")

# Set up OpenAI API
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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

# 🔹 Function to Check with OpenAI (Updated for v1 API)
async def check_fake_news_with_openai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Is the following statement misinformation? Provide a short explanation:\n{text}"}]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return "⚠️ Error retrieving AI analysis."

# 🔹 Function to Detect Fake News and Get AI Feedback
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, response in fake_news_keywords.items():
        if re.search(pattern, text):
            # Get AI analysis
            ai_analysis = await check_fake_news_with_openai(text)

            try:
                # Try to send the meme image with AI analysis
                await update.message.reply_photo(
                    photo=response["meme"], 
                    caption=f"{response['text']}\n\n🧠 AI Analysis:\n{ai_analysis}"
                )
            except Exception as e:
                # If the meme fails, send only text
                await update.message.reply_text(f"{response['text']}\n\n🧠 AI Analysis:\n{ai_analysis}")
                logging.error(f"Error sending meme for '{text}': {e}")

            return

    # If no keyword is matched, just return AI analysis
    ai_analysis = await check_fake_news_with_openai(text)
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

# 🔹 Main Function
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    app.add_error_handler(error_handler)

    # Run Bot
    app.run_polling()

if __name__ == "__main__":
    main()
