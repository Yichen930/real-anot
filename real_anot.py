#real_anot.py
import logging
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from deepfake_detector import analyse_video
from fake_news_checker import detect_fake_news, analyze_news_with_ai, classify_with_ai

TELEGRAM_BOT_TOKEN = "7661066348:AAGg5mRhCFRagqjyswHRVDgtHEBuBqut5gw"

# Set up logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# Function to handle video messages
async def handle_video(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🔍 Processing video... Please wait.")
    video_file = await update.message.video.get_file()
    video_path = "video.mp4"
    await video_file.download_to_drive(video_path)
    result = analyse_video(video_path)
    await update.message.reply_text(result)
    os.remove(video_path)

# Function to handle text messages (fake news detection)
async def handle_fake_news(update, context):

    text = update.message.text.strip()
    await update.message.reply_text("🕵️ Analyzing text for fake news... Please wait.")
    
    meme_url, category, response_text, ai_analysis = await detect_fake_news(text)
    
    response = (
        f"📚 *Fake News Analysis*\n\n"
        f"🟠 *Category:* {category}\n"
        f"💬 *Response:* {response_text}\n"
        f"🧠 *AI Insights:* {ai_analysis}\n"
    )
    if meme_url:
        response += f"🖼️ *Meme Example:* [View Meme]({meme_url})"

    await update.message.reply_text(response, parse_mode="Markdown")



# Function to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🤖 Welcome! I can help detect deepfakes, fake news, and check URL reliability.\n\n"
        "📹 Send a video to check for deepfakes.\n"
        "📰 Send a message to check for misinformation.\n"
        "🌐 Send a URL to verify its reliability.\n\n"
        "Use /report <message> if you find an incorrect classification.")

# Main function to run the bot
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fake_news))
    logging.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
