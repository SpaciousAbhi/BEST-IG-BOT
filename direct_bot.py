#!/usr/bin/env python3
"""
Instagram Bot using direct Telegram Bot API to avoid time sync issues
"""
import os
import re
import requests
import json
import time
import tempfile
import shutil
import glob
import uuid
import threading
from config import Config

BOT_TOKEN = Config.BOT_TOKEN
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0
        self.running = True
        
    def get_updates(self, offset=None, timeout=10):
        """Get updates from Telegram"""
        url = f"{self.api_url}/getUpdates"
        params = {
            'timeout': timeout,
            'offset': offset
        }
        try:
            response = requests.get(url, params=params, timeout=timeout+5)
            return response.json()
        except Exception as e:
            print(f"Error getting updates: {e}")
            return None
    
    def send_message(self, chat_id, text, parse_mode='Markdown'):
        """Send text message"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error sending message: {e}")
            return None
    
    def send_photo(self, chat_id, photo_path, caption=None):
        """Send photo"""
        url = f"{self.api_url}/sendPhoto"
        try:
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': chat_id}
                if caption:
                    data['caption'] = caption
                response = requests.post(url, files=files, data=data, timeout=30)
            return response.json()
        except Exception as e:
            print(f"Error sending photo: {e}")
            return None
    
    def send_video(self, chat_id, video_path, caption=None):
        """Send video"""
        url = f"{self.api_url}/sendVideo"
        try:
            with open(video_path, 'rb') as video:
                files = {'video': video}
                data = {'chat_id': chat_id}
                if caption:
                    data['caption'] = caption
                response = requests.post(url, files=files, data=data, timeout=60)
            return response.json()
        except Exception as e:
            print(f"Error sending video: {e}")
            return None
    
    def extract_shortcode(self, url):
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
    
    def download_instagram_content(self, url, temp_dir):
        """Download Instagram content"""
        try:
            shortcode = self.extract_shortcode(url)
            if not shortcode:
                return False, "Invalid Instagram URL format"

            # Try multiple methods
            methods = [
                f"https://www.instagram.com/p/{shortcode}/embed/",
                f"https://www.instagram.com/p/{shortcode}/",
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            for method_url in methods:
                try:
                    response = requests.get(method_url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        content = response.text
                        downloaded = 0
                        
                        # Find media URLs with better patterns
                        patterns = [
                            r'"display_url":"([^"]+)"',
                            r'"video_url":"([^"]+)"',
                            r'src="([^"]+\.jpg[^"]*)"',
                            r'content="([^"]*scontent[^"]*\.jpg[^"]*)"'
                        ]
                        
                        found_urls = set()
                        
                        for pattern in patterns:
                            matches = re.findall(pattern, content)
                            for match in matches:
                                if 'instagram' in match or 'fbcdn' in match:
                                    found_urls.add(match.replace('\\u0026', '&'))
                        
                        # Download found media
                        for i, media_url in enumerate(list(found_urls)[:5]):  # Limit to 5
                            try:
                                media_response = requests.get(media_url, headers=headers, timeout=30)
                                
                                if media_response.status_code == 200 and len(media_response.content) > 1000:
                                    extension = '.jpg' if any(ext in media_url.lower() for ext in ['.jpg', 'jpg']) else '.mp4'
                                    filename = f"{temp_dir}/media_{i+1}{extension}"
                                    
                                    with open(filename, 'wb') as f:
                                        f.write(media_response.content)
                                    downloaded += 1
                                    print(f"Downloaded: {filename}")
                                    
                            except Exception as e:
                                print(f"Failed to download media {i}: {e}")
                                continue
                        
                        if downloaded > 0:
                            return True, f"Downloaded {downloaded} files"
                            
                except Exception as e:
                    print(f"Method {method_url} failed: {e}")
                    continue
            
            return False, "Could not extract media from Instagram post"
            
        except Exception as e:
            return False, f"Download error: {str(e)}"
    
    def handle_message(self, message):
        """Handle incoming message"""
        try:
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            print(f"Received message from {chat_id}: {text}")
            
            if text == '/start':
                welcome_text = """🤖 **Instagram Downloader Bot**

✅ Bot is online and working!

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
                self.send_message(chat_id, welcome_text)
                
            elif text == '/help':
                help_text = """📋 **Help Guide**

**How to use:**
1. Copy Instagram URL from app/website
2. Send the URL to this bot
3. Wait for download and upload

**Supported URLs:**
• Posts: `instagram.com/p/ABC123/`
• Reels: `instagram.com/reel/XYZ789/`
• IGTV: `instagram.com/tv/ABC123/`

**Tips:**
• Works best with public content
• Large files may take time
• Bot will retry failed downloads

Send me an Instagram URL to test! 🎯"""
                self.send_message(chat_id, help_text)
                
            elif text == '/status':
                status_text = """📊 **Bot Status**

✅ **Online and Ready**
🔄 Instagram downloader active
📥 Processing public content
📤 Direct upload to Telegram

**Current capabilities:**
• Instagram posts ✅
• Instagram reels ✅
• Instagram IGTV ✅
• Error handling ✅

Ready to download! Send an Instagram URL."""
                self.send_message(chat_id, status_text)
                
            elif 'instagram.com' in text.lower():
                url = text.strip()
                
                # Send processing message
                self.send_message(chat_id, "🔄 **Processing Instagram URL...**\n\n⏳ Extracting content...")
                
                # Create temp directory
                temp_dir = f"/tmp/ig_{chat_id}_{uuid.uuid4().hex[:8]}"
                os.makedirs(temp_dir, exist_ok=True)
                
                try:
                    success, result_message = self.download_instagram_content(url, temp_dir)
                    
                    if success:
                        self.send_message(chat_id, "📤 **Uploading files...**")
                        
                        # Upload files
                        images = glob.glob(f"{temp_dir}/*.jpg")
                        videos = glob.glob(f"{temp_dir}/*.mp4")
                        
                        uploaded = 0
                        
                        # Send images
                        for image in images:
                            if os.path.getsize(image) > 1000:  # At least 1KB
                                result = self.send_photo(chat_id, image, "📸 Downloaded from Instagram")
                                if result and result.get('ok'):
                                    uploaded += 1
                                time.sleep(0.5)  # Rate limiting
                        
                        # Send videos
                        for video in videos:
                            if os.path.getsize(video) > 1000:  # At least 1KB
                                result = self.send_video(chat_id, video, "🎥 Downloaded from Instagram")
                                if result and result.get('ok'):
                                    uploaded += 1
                                time.sleep(0.5)  # Rate limiting
                        
                        if uploaded > 0:
                            self.send_message(chat_id, f"✅ **Success!** Sent {uploaded} files from Instagram post.")
                        else:
                            self.send_message(chat_id, "❌ No valid files found to upload.")
                    else:
                        error_msg = f"""❌ **Download Failed**

{result_message}

**Common reasons:**
• Content is private or restricted
• Instagram blocking requests
• Post was deleted
• Network issues

**What to try:**
✅ Make sure the post is public
✅ Try a different Instagram URL
✅ Wait a few minutes and retry
✅ Check the URL format

**Supported formats:**
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`"""
                        self.send_message(chat_id, error_msg)
                        
                except Exception as e:
                    self.send_message(chat_id, f"❌ **Unexpected Error:** {str(e)}")
                    print(f"Error processing {url}: {e}")
                finally:
                    # Cleanup
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
            else:
                # Unknown message
                self.send_message(chat_id, """🤔 **Unknown command**

I can help you download Instagram content!

**Available commands:**
• `/start` - Main menu
• `/help` - Usage guide
• `/status` - Bot status

**Or just send me any Instagram URL:**
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`

Try sending an Instagram link! 🚀""")
                
        except Exception as e:
            print(f"Error handling message: {e}")
    
    def start_polling(self):
        """Start polling for updates"""
        print("🚀 Starting Instagram Bot with polling...")
        print(f"🔑 Bot Token: {self.token[:20]}...")
        
        # Test bot token first
        me = requests.get(f"{self.api_url}/getMe").json()
        if me.get('ok'):
            bot_info = me['result']
            print(f"✅ Bot connected: @{bot_info['username']} ({bot_info['first_name']})")
        else:
            print("❌ Bot token is invalid!")
            return
        
        print("📡 Starting to poll for messages...")
        
        while self.running:
            try:
                updates = self.get_updates(offset=self.last_update_id + 1, timeout=10)
                
                if updates and updates.get('ok'):
                    for update in updates['result']:
                        self.last_update_id = update['update_id']
                        
                        if 'message' in update:
                            self.handle_message(update['message'])
                else:
                    print("⚠️ No updates or error getting updates")
                    
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Polling error: {e}")
                time.sleep(5)  # Wait before retrying
        
        print("✅ Bot stopped.")

if __name__ == '__main__':
    bot = TelegramBot(BOT_TOKEN)
    bot.start_polling()