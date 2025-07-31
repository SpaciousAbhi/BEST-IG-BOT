"""
Instagram Content Downloader Bot - Fixed Version
Handles time sync issues and webhook problems properly
"""

import os
import re
import asyncio
import tempfile
import shutil
import glob
import uuid
import requests
from pyrogram import Client, filters
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.errors import BadMsgNotification, FloodWait
from config import Config
import time

print("📋 Bot Configuration:")
print(f"🔑 API ID: {Config.API_ID}")
print(f"🤖 Bot Token: {Config.BOT_TOKEN[:20]}...")

# Create bot with better error handling
app = Client(
    "instagram_bot_session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir="/tmp",
    sleep_threshold=60
)

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

def extract_username(url):
    """Extract username from Instagram profile URL"""
    match = re.search(r'instagram\.com/([A-Za-z0-9_.]+)/?$', url)
    return match.group(1) if match else None

async def download_instagram_content(url, temp_dir):
    """Simple Instagram content downloader using web scraping"""
    try:
        # Method 1: Try embed page
        shortcode = extract_shortcode(url)
        if shortcode:
            embed_url = f"https://www.instagram.com/p/{shortcode}/embed/"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(embed_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Simple regex to find image/video URLs in the embed page
                content = response.text
                
                # Look for image URLs
                image_patterns = [
                    r'"display_url":"([^"]+)"',
                    r'"url":"([^"]+\.jpg[^"]*)"',
                    r'src="([^"]+\.jpg[^"]*)"'
                ]
                
                video_patterns = [
                    r'"video_url":"([^"]+)"',
                    r'"url":"([^"]+\.mp4[^"]*)"'
                ]
                
                media_found = False
                
                # Try to find and download images
                for pattern in image_patterns:
                    matches = re.findall(pattern, content)
                    for i, match in enumerate(matches[:3]):  # Limit to 3 images
                        try:
                            media_url = match.replace('\\u0026', '&')
                            media_response = requests.get(media_url, headers=headers, timeout=15)
                            if media_response.status_code == 200:
                                filename = f"{temp_dir}/image_{i+1}.jpg"
                                with open(filename, 'wb') as f:
                                    f.write(media_response.content)
                                media_found = True
                        except Exception as e:
                            print(f"Failed to download image {i+1}: {e}")
                            continue
                
                # Try to find and download videos
                for pattern in video_patterns:
                    matches = re.findall(pattern, content)
                    for i, match in enumerate(matches[:2]):  # Limit to 2 videos
                        try:
                            media_url = match.replace('\\u0026', '&')
                            media_response = requests.get(media_url, headers=headers, timeout=30)
                            if media_response.status_code == 200:
                                filename = f"{temp_dir}/video_{i+1}.mp4"
                                with open(filename, 'wb') as f:
                                    f.write(media_response.content)
                                media_found = True
                        except Exception as e:
                            print(f"Failed to download video {i+1}: {e}")
                            continue
                
                return media_found
        
        return False
        
    except Exception as e:
        print(f"Download error: {e}")
        return False

async def upload_files(client, chat_id, temp_dir, status_msg):
    """Upload downloaded files to Telegram"""
    try:
        images = glob.glob(f"{temp_dir}/*.jpg") + glob.glob(f"{temp_dir}/*.jpeg")
        videos = glob.glob(f"{temp_dir}/*.mp4")
        
        total = len(images) + len(videos)
        if total == 0:
            await status_msg.edit_text("❌ No files found to upload.")
            return
            
        uploaded = 0
        
        # Upload images
        for image in images:
            try:
                await client.send_photo(chat_id, image)
                uploaded += 1
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Failed to upload image: {e}")
                
        # Upload videos
        for video in videos:
            try:
                await client.send_video(chat_id, video)
                uploaded += 1
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Failed to upload video: {e}")
                
        await status_msg.edit_text(f"✅ Successfully uploaded {uploaded} files!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = """🤖 **Instagram Downloader Bot**

Send me Instagram links and I'll download them for you!

**Supported:**
📸 Posts & Photos
🎥 Reels & Videos  
🖼️ IGTV Videos

**Usage:**
Just send any Instagram URL like:
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`

**Note:** This bot works best with public content.

Try sending me an Instagram URL! 🚀"""
    await message.reply_text(text)

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    text = """📋 **Help**

**How to use:**
1. Send me any Instagram URL
2. I'll try to download it automatically
3. Files will be sent back to you

**Supported URLs:**
• Posts: instagram.com/p/ABC123/
• Reels: instagram.com/reel/XYZ789/
• IGTV: instagram.com/tv/ABC123/

**Notes:**
• Some content may not be downloadable
• Large files may take time to process
• Bot works best with public content

Send /start to see the main menu!"""
    await message.reply_text(text)

@app.on_message(filters.regex(r'instagram\.com'))
async def handle_url(client, message):
    url = message.text.strip()
    status = await message.reply_text("🔄 Processing Instagram URL...")
    
    temp_dir = f"/tmp/{message.from_user.id}_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        await status.edit_text("📥 Attempting to download content...")
        
        success = await download_instagram_content(url, temp_dir)
        
        if success:
            await status.edit_text("📤 Uploading files...")
            await upload_files(client, message.chat.id, temp_dir, status)
        else:
            await status.edit_text("""❌ **Download Failed**

This could be because:
• Content is private or restricted
• Instagram is blocking requests
• Invalid URL format

**What you can try:**
1. Make sure the Instagram account is public
2. Try a different post URL
3. Wait a few minutes and try again

**Supported formats:**
✅ https://instagram.com/p/ABC123/
✅ https://instagram.com/reel/XYZ789/
✅ https://instagram.com/tv/ABC123/""")
        
    except Exception as e:
        await status.edit_text(f"❌ Unexpected error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

async def main():
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"🚀 Starting Instagram Bot (attempt {attempt + 1})...")
            await app.start()
            print("✅ Bot started successfully!")
            print("🎯 Bot is ready to receive Instagram URLs!")
            print("📱 Users can now send Instagram links to download content")
            
            # Keep the bot running
            await asyncio.Event().wait()
            
        except BadMsgNotification as e:
            print(f"⚠️ Time synchronization error: {e}")
            if attempt < max_retries - 1:
                print(f"⏰ Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("❌ Failed after all retries. Time sync issue persists.")
                raise
                
        except Exception as e:
            print(f"❌ Bot error: {e}")
            if attempt < max_retries - 1:
                print(f"🔄 Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("❌ Bot failed to start after all retries.")
                raise
    
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())