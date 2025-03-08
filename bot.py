import os
import requests
from openai import OpenAI  # ✅ 使用 OpenAI 官方 SDK
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import re
import logging

# 🔹 启用日志记录
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# 🔹 获取环境变量
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Telegram 机器人 Token
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # OpenAI API Key

# ✅ 确保 API Key 存在
if not TELEGRAM_TOKEN:
    raise ValueError("❌ MISSING TELEGRAM_BOT_TOKEN environment variable!")
if not OPENAI_API_KEY:
    raise ValueError("❌ MISSING OPENAI_API_KEY environment variable!")

# 🔹 初始化 OpenAI 客户端
client = OpenAI(api_key=OPENAI_API_KEY)

# 🔹 假新闻关键词 & Meme 响应
fake_news_keywords = {
    # 1️⃣ 阴谋论
    r"aliens|UFO|extraterrestrial": {
        "text": "⚠️ So… aliens are responsible for this too? 👽",
        "meme": "https://i.imgflip.com/1bij.jpg"
    },
    r"government secret|hiding something|deep state|they don’t want you to know": {
        "text": "🚨 Ah yes, another 'they don’t want you to know this' moment. 😏",
        "meme": "https://i.imgflip.com/4t0m5.jpg"
    },

    # 2️⃣ 健康假新闻
    r"trust me, I’m a doctor|miracle cure|big pharma is lying": {
        "text": "🧐 Oh, you have a PhD in WhatsApp Forwarding?",
        "meme": "https://i.imgflip.com/26am.jpg"
    },
    r"I did my own research|natural remedies|essential oils cure everything": {
        "text": "🔬 And by research, you mean watching a YouTube video?",
        "meme": "https://i.imgflip.com/5g9o3h.jpg"
    },

    # 3️⃣ AI 生成的假新闻
    r"AI generated|deepfake|fake video|too realistic": {
        "text": "🤔 This looks AI-generated… because it is.",
        "meme": "https://i.imgflip.com/4c1p.jpg"
    },

    # 4️⃣ 伪科学
    r"quantum energy|frequencies|5G is dangerous": {
        "text": "🧠 This post used 'quantum' and 'frequencies,' so it must be legit?",
        "meme": "https://i.imgflip.com/2h3r.jpg"
    },

    # 5️⃣ 政治假新闻
    r"fake news|biased media|propaganda|mainstream media is lying": {
        "text": "🤨 You sure this isn’t propaganda disguised as 'news'?",
        "meme": "https://i.imgflip.com/3w7cva.jpg"
    },

    # 6️⃣ 旧新闻被重新包装
    r"breaking news|shocking discovery|you won’t believe": {
        "text": "😂 BREAKING: This event happened… 10 years ago.",
        "meme": "https://i.imgflip.com/39t1o.jpg"
    },

    # 7️⃣ 标题党 & 虚假新闻
    r"scientists hate this|banned information|they don’t want you to know": {
        "text": "😆 Clickbait title: 'Scientists HATE this simple trick!'",
        "meme": "https://i.imgflip.com/30b1gx.jpg"
    },
}

# 🔹 发送请求到 OpenAI API 进行假新闻检测
async def check_fake_news_with_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # ✅ 使用 OpenAI 官方最新模型
            messages=[{"role": "user", "content": f"Is the following statement misinformation? Provide a short explanation:\n{text}"}],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return f"⚠️ Error retrieving AI analysis: {str(e)}"

# 🔹 处理假新闻检测
async def detect_fake_news(update: Update, context: CallbackContext) -> None:
    text = update.message.text.lower()

    for pattern, response in fake_news_keywords.items():
        if re.search(pattern, text):
            ai_analysis = await check_fake_news_with_ai(text)

            try:
                await update.message.reply_photo(
                    photo=response["meme"],
                    caption=f"{response['text']}\n\n🧠 AI Analysis:\n{ai_analysis}"
                )
            except Exception as e:
                await update.message.reply_text(f"{response['text']}\n\n🧠 AI Analysis:\n{ai_analysis}")
                logging.error(f"❌ Error sending meme for '{text}': {e}")
            return

    ai_analysis = await check_fake_news_with_ai(text)
    await update.message.reply_text(f"🧠 AI Analysis:\n{ai_analysis}")

# 🔹 机器人 `/start` 命令
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the Fake News Meme Bot! 🤖\n"
        "Send me a message, and I'll check if it's fake news."
    )

# 🔹 错误处理
async def error_handler(update: object, context: CallbackContext) -> None:
    logging.error(f"❌ Update {update} caused error {context.error}")

# 🔹 主程序（使用 Webhook）
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # 处理命令和消息
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, detect_fake_news))
    app.add_error_handler(error_handler)

    # ✅ 轮询模式（如果你想使用 Webhook，替换 `run_polling()`）
    app.run_polling()

if __name__ == "__main__":
    main()
