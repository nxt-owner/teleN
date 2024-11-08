import requests
from bs4 import BeautifulSoup
import time
import os

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN = '7857441004:AAEZnfkRs-uSFSSjMzdmDHH1cJpTflVioio'
CHANNEL_ID = '@news_SL1'
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Variable to store the last sent news ID
last_sent_news_id = None

def fetch_latest_news():
    url = 'https://esana.com.lk/c/read'
    response = requests.get(url)
    if response.status_code != 200:
        print(f'Failed to fetch the page. Status code: {response.status_code}')
        return None, None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    news_blocks = soup.find_all('div', class_='post-block')
    latest_news = None
    latest_id = -1  # To track the highest ID

    for news in news_blocks:
        # Extract link and find the numeric ID
        link_tag = news.find('a', href=True)
        link = f"https://esana.com.lk/{link_tag['href']}" if link_tag else None
        if not link:
            continue
        
        # Extract the numeric part of the URL
        try:
            news_id = int(link.split('/')[-1])  # Gets the number at the end of the URL, e.g., 104870
        except ValueError:
            continue  # Skip if the ID is not a number

        # Extract news title
        title_tag = news.find('h3', class_='axil-post-title')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"

        # Extract image URL
        image_tag = news.find('img')
        image_url = image_tag['src'] if image_tag else None

        # Extract time
        time_tag = news.find('div', class_='post-metas').find('a')
        time_text = time_tag.get_text(strip=True) if time_tag else "Unknown time"

        # Check if this is the latest news based on the ID
        if news_id > latest_id:
            latest_id = news_id
            latest_news = (title, f"Latest News: {title}\nPosted: {time_text}\nLink: {link}", image_url)

    return latest_news if latest_news else (None, None, None), latest_id

def send_to_telegram(message, image_url=None):
    """Send message to the Telegram channel with an image as the main post and text as caption."""
    if image_url:
        # Send the image with the message as a caption
        try:
            telegram_api_url = f"{BASE_URL}/sendPhoto"
            payload = {
                'chat_id': CHANNEL_ID,
                'caption': message,
                'parse_mode': 'Markdown'
            }
            files = {'photo': requests.get(image_url).content}
            response = requests.post(telegram_api_url, data=payload, files=files)
            print(f"Response: {response.status_code}, {response.text}")
            return response.ok
        except Exception as e:
            print(f"Failed to send image to Telegram. Error: {e}")
            return False
    else:
        # Send only text if no image URL is provided
        telegram_api_url = f"{BASE_URL}/sendMessage"
        payload = {
            'chat_id': CHANNEL_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(telegram_api_url, json=payload)
        return response.ok

# Monitor for new news every 5 minutes
while True:
    result, latest_id = fetch_latest_news()
    
    if result is None:
        print("No news found or failed to fetch news.")
    else:
        title, news_message, image_url = result
        if latest_id and latest_id != last_sent_news_id:  # Check if this news ID has already been sent
            if send_to_telegram(news_message, image_url):
                print(f"Sent to Telegram: {news_message}")
            else:
                print("Failed to send to Telegram.")
            last_sent_news_id = latest_id  # Update the last sent news ID
        else:
            print("No new news to send.")
    time.sleep(30)  # Wait 30S before checking again
