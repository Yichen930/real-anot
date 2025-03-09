#real_anot.py
import logging
import os
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from deepfake_detector import analyse_video
from fake_news_checker import detect_fake_news

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

async def handle_video(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🔍 Processing video... Please wait.")
    video_file = await update.message.video.get_file()
    
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
        video_path = temp_video.name
        await video_file.download(custom_path=video_path)
    
    result = analyse_video(video_path)
    await update.message.reply_text(result)
    
    os.remove(video_path)  

async def handle_fake_news(update: Update, context: CallbackContext) -> None:
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

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "🤖 Welcome! I can help detect deepfakes, fake news, and check URL reliability.\n\n"
        "📹 Send a video to check for deepfakes.\n"
        "📰 Send a message to check for misinformation.\n"
        "🌐 Send a URL to verify its reliability.\n\n"
        "Use /report <message> if you find an incorrect classification."
    )

def main():
    if not TELEGRAM_TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN is missing. Please set the environment variable.")
        return
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_fake_news))
    
    logging.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
