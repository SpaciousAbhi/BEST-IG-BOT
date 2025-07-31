#!/usr/bin/env python3
"""
Instagram Bot using Webhook instead of polling to avoid time sync issues
"""
import os
import re
import requests
import json
from flask import Flask, request, jsonify
from config import Config
import tempfile
import shutil
import glob
import uuid

app = Flask(__name__)

BOT_TOKEN = Config.BOT_TOKEN
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    """Send message via Telegram Bot API"""
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def send_telegram_photo(chat_id, photo_path):
    """Send photo via Telegram Bot API"""
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': chat_id}
            response = requests.post(url, files=files, data=data, timeout=30)
        return response.json()
    except Exception as e:
        print(f"Error sending photo: {e}")
        return None

def send_telegram_video(chat_id, video_path):
    """Send video via Telegram Bot API"""
    url = f"{TELEGRAM_API_URL}/sendVideo"
    try:
        with open(video_path, 'rb') as video:
            files = {'video': video}
            data = {'chat_id': chat_id}
            response = requests.post(url, files=files, data=data, timeout=60)
        return response.json()
    except Exception as e:
        print(f"Error sending video: {e}")
        return None

def extract_shortcode(url):
    """Extract shortcode from Instagram URL"""
    patterns = [
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'instagram\.com/tv/([A-Za-z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_instagram_content(url, temp_dir):
    """Simple Instagram content downloader"""
    try:
        shortcode = extract_shortcode(url)
        if not shortcode:
            return False, "Invalid Instagram URL"

        # Try embed method
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(embed_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            content = response.text
            downloaded = 0
            
            # Find media URLs
            patterns = [
                r'"display_url":"([^"]+)"',
                r'"video_url":"([^"]+)"',
                r'src="([^"]+\.jpg[^"]*)"'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for i, match in enumerate(matches[:5]):  # Limit to 5 files
                    try:
                        media_url = match.replace('\\u0026', '&')
                        media_response = requests.get(media_url, headers=headers, timeout=30)
                        
                        if media_response.status_code == 200:
                            extension = '.jpg' if 'jpg' in media_url else '.mp4'
                            filename = f"{temp_dir}/media_{i+1}{extension}"
                            
                            with open(filename, 'wb') as f:
                                f.write(media_response.content)
                            downloaded += 1
                    except Exception as e:
                        print(f"Failed to download media {i}: {e}")
                        continue
            
            return downloaded > 0, f"Downloaded {downloaded} files"
        else:
            return False, f"Instagram returned {response.status_code}"
            
    except Exception as e:
        return False, f"Download error: {str(e)}"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Telegram webhook"""
    try:
        update = request.get_json()
        
        if not update or 'message' not in update:
            return jsonify({'ok': True})
        
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        # Handle /start command
        if text == '/start':
            welcome_text = """🤖 **Instagram Downloader Bot**

Send me Instagram links and I'll download them for you!

**Supported:**
📸 Posts & Photos
🎥 Reels & Videos  
📺 IGTV Videos

**Usage:**
Just send any Instagram URL like:
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`

Try it now! 🚀"""
            send_telegram_message(chat_id, welcome_text)
            return jsonify({'ok': True})
        
        # Handle /help command
        if text == '/help':
            help_text = """📋 **Help**

**How to use:**
1. Send me any Instagram URL
2. I'll download it automatically
3. Files will be sent back to you

**Supported URLs:**
• Posts: instagram.com/p/ABC123/
• Reels: instagram.com/reel/XYZ789/
• IGTV: instagram.com/tv/ABC123/

**Note:** Works best with public content."""
            send_telegram_message(chat_id, help_text)
            return jsonify({'ok': True})
        
        # Handle Instagram URLs
        if 'instagram.com' in text:
            url = text.strip()
            
            # Send processing message
            send_telegram_message(chat_id, "🔄 Processing Instagram URL...")
            
            # Create temp directory
            temp_dir = f"/tmp/ig_{chat_id}_{uuid.uuid4().hex[:8]}"
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                success, message_text = download_instagram_content(url, temp_dir)
                
                if success:
                    # Upload files
                    images = glob.glob(f"{temp_dir}/*.jpg")
                    videos = glob.glob(f"{temp_dir}/*.mp4")
                    
                    uploaded = 0
                    
                    # Send images
                    for image in images:
                        if os.path.getsize(image) > 1000:  # At least 1KB
                            if send_telegram_photo(chat_id, image):
                                uploaded += 1
                    
                    # Send videos
                    for video in videos:
                        if os.path.getsize(video) > 1000:  # At least 1KB
                            if send_telegram_video(chat_id, video):
                                uploaded += 1
                    
                    if uploaded > 0:
                        send_telegram_message(chat_id, f"✅ Successfully sent {uploaded} files!")
                    else:
                        send_telegram_message(chat_id, "❌ No valid files found to send.")
                else:
                    error_msg = f"""❌ **Download Failed**

{message_text}

**Possible reasons:**
• Content is private or restricted
• Instagram is blocking requests
• Invalid URL format

**Try:**
• Make sure the post is public
• Try a different Instagram URL
• Wait a few minutes and retry"""
                    send_telegram_message(chat_id, error_msg)
                    
            except Exception as e:
                send_telegram_message(chat_id, f"❌ Error: {str(e)}")
            finally:
                # Cleanup
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        
        return jsonify({'ok': True})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'ok': True})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'bot': 'instagram_downloader'})

if __name__ == '__main__':
    print("🚀 Starting Instagram Bot Webhook Server...")
    print(f"🔑 Using Bot Token: {BOT_TOKEN[:20]}...")
    
    # Set webhook (commented out for now, needs public URL)
    # webhook_url = "YOUR_PUBLIC_URL/webhook" 
    # requests.post(f"{TELEGRAM_API_URL}/setWebhook", json={'url': webhook_url})
    
    app.run(host='0.0.0.0', port=8000, debug=False)