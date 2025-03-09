import os
import re
import json
import logging
from openai import OpenAI

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

OPENAI_API_KEY ="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"
if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY environment variable")

client = OpenAI(api_key=OPENAI_API_KEY)

# Meme responses mapped to regex-detected categories
fake_news_keywords = {
    r"\b(aliens?|UFO|extraterrestrial|area[\s-]?51|reptilian|illuminati|new[\s-]?world[\s-]?order)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/1bij.jpg", "👽 So… aliens did this too? Classic!"),
    
    r"\b(government secret|deep[\s-]?state|hidden[\s-]?agenda|they don'?t want you to know|cover[\s-]?up|black[\s-]?ops)\b": 
        ("Conspiracy Theory", "https://i.imgflip.com/4t0m5.jpg", "🚨 Another 'They don't want you to know this' moment. 🤔"),
    
    r"\b(trust me, I'?m a doctor|miracle cure|big[\s-]?pharma|natural[\s-]?medicine|homeopathy|detox|superfood|cancer[\s-]?cure)\b": 
        ("Fake Health News", "https://i.imgflip.com/26am.jpg", "🧐 Oh, you have a PhD in WhatsApp Forwarding?"),
    
    r"\b(vaccines? (cause|lead to|linked to) autism|anti[\s-]?vax|vaccine[\s-]?hoax|big[\s-]?pharma|doctors are lying)\b": 
        ("Fake Health News", "https://i.imgflip.com/26am.jpg", "🧐 Oh, you have a PhD in WhatsApp Forwarding?"),

    r"\b(5G (towers?|networks?) (are|is) (dangerous|making people sick|causing cancer)|radiation[\s-]?harm|electromagnetic[\s-]?weapon|phone signals cause cancer)\b": 
        ("Fake Science Claim", "https://blogs.prio.org/wp-content/uploads/2017/05/34079489601_0af732b619_k.jpg", "🧠 'Quantum' and 'frequencies' = must be real science, right?"),

    r"\b(the election (was|is) (rigged|stolen|manipulated) by (secret elites|deep state|globalists)|voter manipulation|illegal voting|stolen election)\b": 
        ("Political Misinformation", "https://misinforeview.hks.harvard.edu/wp-content/uploads/2021/08/fig1_new-1536x1384.png", "🤨 Are you sure this isn’t propaganda?"),

    r"\b(breaking[:!?]?\s*(scientists? (discover|found|identify|detect))|shocking discovery|scientists (discover|found) .* (years ago|in \d{4})|\(article from \d{4}\)|exposed after years)\b": 
        ("Old News Reused", "https://i.imgflip.com/39t1o.jpg", "😂 BREAKING: This event happened… a decade ago."),

    r"\b(you won'?t believe (what|how|why) .* (just|recently)? (found|discovered|exposed|revealed|uncovered|hidden) (under the ocean|in the jungle|in Antarctica|in space|in the desert|on an island|on the moon)|shocking discovery|hidden treasure|mystery solved|forbidden knowledge)\b": 
        ("Clickbait & Fake News", "https://i.imgflip.com/30b1gx.jpg", "😆 Clickbait alert! 'Scientists HATE this one trick!'"),

    r"\b(mainstream[\s-]?media (is|are) (lying|spreading propaganda|misleading|hiding the truth|fake)|fake[\s-]?news|biased[\s-]?media|media blackout|propaganda machine)\b": 
        ("Media Misinformation", "https://i.imgflip.com/4t0m5.jpg", "📰 The media must be lying again, right?"),
}

# AI analyzes the text but does not pick the category
async def analyze_news_with_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                    "You are a fact-checking assistant. "
                    "Analyze the following text and provide a brief analysis of whether it contains misinformation or exaggerations."
                    "Do NOT categorize it—just provide a factual analysis."},
                {"role": "user", "content": text}
            ],
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return "⚠️ Error retrieving AI analysis."

# Detect fake news using regex + AI analysis
async def detect_fake_news(text):
    text = text.lower()

    # Check for fake news using predefined regex
    for pattern, (category, meme_url, response_text) in fake_news_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            ai_analysis = await analyze_news_with_ai(text)
            return meme_url, category, response_text, ai_analysis
    
    ai_category, ai_meme_url, ai_response_text = await classify_with_ai(text)

    ai_analysis = await analyze_news_with_ai(text)
    return ai_meme_url, ai_category, ai_response_text, ai_analysis

# Classify text into AI-detected categories
async def classify_with_ai(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                    "You are a misinformation detection assistant. "
                    "Analyze the following text and classify it into one of these categories:\n\n"
                    "1. Conspiracy Theory\n"
                    "2. Fake Health News\n"
                    "3. AI-Generated Misinformation\n"
                    "4. Fake Science Claim\n"
                    "5. Political Misinformation\n"
                    "6. Old News Reused\n"
                    "7. Clickbait & Fake News\n\n"
                    "If the text does not fit any category, return 'Unknown'."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )

        category = response.choices[0].message.content.strip()

        if category in fake_news_keywords:
            meme_url = fake_news_keywords[category][1]
            response_text = fake_news_keywords[category][2]
        else:
            category = "Unknown"
            meme_url = "https://i.imgflip.com/30b1gx.jpg"
            response_text = "🤔 I couldn't classify this. Could you clarify?"

        return category, meme_url, response_text

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return "Error", "https://i.imgflip.com/30b1gx.jpg", "⚠️ AI Classification Failed."


