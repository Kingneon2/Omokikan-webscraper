import os
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = os.environ.get("8872266502:AAEBGkFSo5aOzjvU3WY0ol_cCpDce5hq-vA")
TELEGRAM_API = f"https://api.telegram.org/bot{8872266502:AAEBGkFSo5aOzjvU3WY0ol_cCpDce5hq-vA}"

URL_REGEX = re.compile(r"https?://[^\s]+")


def send_message(chat_id, text):
    requests.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=10,
    )


def scrape_url(url):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Couldn't fetch that page: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "No title found"

    desc_tag = soup.find("meta", attrs={"name": "description"})
    if not desc_tag:
        desc_tag = soup.find("meta", attrs={"property": "og:description"})
    description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else "No description found"

    # grab a text preview from the body
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    body_text = soup.get_text(separator=" ", strip=True)
    preview = body_text[:500] + ("..." if len(body_text) > 500 else "")

    return (
        f"Title: {title}\n\n"
        f"Description: {description}\n\n"
        f"Preview: {preview}"
    )


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True) or {}
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return "ok"

    if text.startswith("/start"):
        send_message(chat_id, "Send me any link and I'll scrape it for you.")
        return "ok"

    match = URL_REGEX.search(text)
    if not match:
        send_message(chat_id, "Send me a valid URL (starting with http:// or https://).")
        return "ok"

    url = match.group(0)
    send_message(chat_id, "Scraping...")
    result = scrape_url(url)
    send_message(chat_id, result)
    return "ok"


@app.route("/", methods=["GET"])
def health():
    return "Bot is running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  
