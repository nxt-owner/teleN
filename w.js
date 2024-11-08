const axios = require('axios');
const cheerio = require('cheerio');
const fetch = require('node-fetch');
const fs = require('fs');

// Telegram Bot configuration
const TELEGRAM_BOT_TOKEN = '7857441004:AAEZnfkRs-uSFSSjMzdmDHH1cJpTflVioio';
const CHANNEL_ID = '@news_SL1';
const BASE_URL = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}`;

// Variable to store the last sent news ID
let lastSentNewsId = null;

// Fetch the latest news
async function fetchLatestNews() {
    const url = 'https://esana.com.lk/c/read';

    try {
        const response = await axios.get(url);
        if (response.status !== 200) {
            console.log(`Failed to fetch the page. Status code: ${response.status}`);
            return [null, null, null];
        }

        const $ = cheerio.load(response.data);
        const newsBlocks = $('div.post-block');
        let latestNews = null;
        let latestId = -1;

        newsBlocks.each((index, element) => {
            const link = $(element).find('a').attr('href');
            if (!link) return;

            const newsId = parseInt(link.split('/').pop(), 10);
            if (isNaN(newsId)) return;

            const title = $(element).find('h3.axil-post-title').text().trim() || 'No Title';
            const imageUrl = $(element).find('img').attr('src') || null;
            const timeText = $(element).find('div.post-metas a').text().trim() || 'Unknown time';
            const fullLink = `https://esana.com.lk/${link}`;

            if (newsId > latestId) {
                latestId = newsId;
                latestNews = { title, message: `Latest News: ${title}\nPosted: ${timeText}\nLink: ${fullLink}`, imageUrl };
            }
        });

        return latestNews ? [latestNews, latestId] : [null, null];
    } catch (error) {
        console.error('Error fetching the page:', error);
        return [null, null, null];
    }
}

// Send message to Telegram with optional image
async function sendToTelegram(message, imageUrl = null) {
    try {
        if (imageUrl) {
            // Download the image
            const imageResponse = await fetch(imageUrl);
            const imageBuffer = await imageResponse.buffer();

            const form = new FormData();
            form.append('chat_id', CHANNEL_ID);
            form.append('caption', message);
            form.append('parse_mode', 'Markdown');
            form.append('photo', imageBuffer, 'image.jpg');

            const telegramApiUrl = `${BASE_URL}/sendPhoto`;
            const response = await axios.post(telegramApiUrl, form, { headers: form.getHeaders() });
            console.log(`Response: ${response.status}, ${response.data}`);
            return response.status === 200;
        } else {
            // Send only text if no image URL is provided
            const telegramApiUrl = `${BASE_URL}/sendMessage`;
            const response = await axios.post(telegramApiUrl, {
                chat_id: CHANNEL_ID,
                text: message,
                parse_mode: 'Markdown',
            });
            return response.status === 200;
        }
    } catch (error) {
        console.error('Error sending to Telegram:', error);
        return false;
    }
}

// Monitor for new news every 30 seconds
setInterval(async () => {
    const [latestNews, latestId] = await fetchLatestNews();
    if (latestNews && latestId && latestId !== lastSentNewsId) {
        const { title, message, imageUrl } = latestNews;
        if (await sendToTelegram(message, imageUrl)) {
            console.log(`Sent to Telegram: ${message}`);
        } else {
            console.log("Failed to send to Telegram.");
        }
        lastSentNewsId = latestId; // Update the last sent news ID
    } else {
        console.log("No new news to send.");
    }
}, 30000);  // Wait 30 seconds before checking again
