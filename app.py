import os
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)

# --- Your bot token (already inserted) ---
BOT_TOKEN = "8872266502:AAH_wYw2A_ItpDjCXuboVHAG6fx9eXUSUjA"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --- URL regex pattern ---
URL_REGEX = re.compile(r"https?://[^\s]+")

def send_message(chat_id, text):
    """Send a message to a Telegram chat."""
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
            timeout=10,
        )
    except Exception as e:
        print(f"Failed to send message: {e}")

def scrape_url(url):
    """Scrape a URL and return title, description, and preview."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"❌ Couldn't fetch that page: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    # Get title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "No title found"

    # Get description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if not desc_tag:
        desc_tag = soup.find("meta", attrs={"property": "og:description"})
    description = desc_tag.get("content", "").strip() if desc_tag and desc_tag.get("content") else "No description found"

    # Get text preview
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = soup.get_text(separator=" ", strip=True)
    preview = body_text[:500] + ("..." if len(body_text) > 500 else "")

    return (
        f"📄 **Title:** {title}\n\n"
        f"📝 **Description:** {description}\n\n"
        f"📖 **Preview:** {preview}"
    )

@app.route("/", methods=["GET"])
def health():
    return "Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming Telegram updates."""
    try:
        update = request.get_json(force=True)
        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id:
            return "ok", 200

        # Find URL in the message
        match = URL_REGEX.search(text)
        if not match:
            send_message(chat_id, "❌ Please send a valid URL.\nExample: `https://example.com`")
            return "ok", 200

        url = match.group(0)
        send_message(chat_id, "🔍 Scraping...")

        result = scrape_url(url)
        send_message(chat_id, result)

        return "ok", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
