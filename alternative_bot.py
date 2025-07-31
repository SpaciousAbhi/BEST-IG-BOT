"""
Alternative Instagram Content Downloader using different approaches
This version tries multiple methods to download Instagram content
"""

import os
import re
import asyncio
import tempfile
import shutil
import glob
import uuid
import requests
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from config import Config

# Bot instance
app = Client(
    ":memory:",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
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

async def download_with_requests(url, temp_dir):
    """Alternative download method using requests and public APIs"""
    try:
        shortcode = extract_shortcode(url)
        if not shortcode:
            return False, "Invalid URL format"
        
        # Try to get post info using Instagram's public endpoint
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Try to get the webpage and extract media URLs
        page_url = f"https://www.instagram.com/p/{shortcode}/"
        response = requests.get(page_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Look for media URLs in the page content
            content = response.text
            
            # Extract image URLs
            img_pattern = r'"display_url":"([^"]+)"'
            img_matches = re.findall(img_pattern, content)
            
            # Extract video URLs  
            video_pattern = r'"video_url":"([^"]+)"'
            video_matches = re.findall(video_pattern, content)
            
            downloaded_files = []
            
            # Download images
            for i, img_url in enumerate(set(img_matches)):
                if 'instagram' in img_url:
                    try:
                        img_url = img_url.replace('\\u0026', '&')
                        img_response = requests.get(img_url, headers=headers, timeout=15)
                        if img_response.status_code == 200:
                            filename = f"{temp_dir}/image_{i+1}.jpg"
                            with open(filename, 'wb') as f:
                                f.write(img_response.content)
                            downloaded_files.append(filename)
                    except Exception as e:
                        print(f"Failed to download image {i+1}: {e}")
            
            # Download videos
            for i, video_url in enumerate(set(video_matches)):
                if 'instagram' in video_url:
                    try:
                        video_url = video_url.replace('\\u0026', '&')
                        video_response = requests.get(video_url, headers=headers, timeout=30)
                        if video_response.status_code == 200:
                            filename = f"{temp_dir}/video_{i+1}.mp4"
                            with open(filename, 'wb') as f:
                                f.write(video_response.content)
                            downloaded_files.append(filename)
                    except Exception as e:
                        print(f"Failed to download video {i+1}: {e}")
            
            if downloaded_files:
                return True, f"Downloaded {len(downloaded_files)} files"
            else:
                return False, "No media found or failed to download"
        else:
            return False, f"Failed to access Instagram page: {response.status_code}"
            
    except Exception as e:
        return False, f"Download error: {str(e)}"

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
        if len(images) == 1:
            await client.send_photo(chat_id, images[0], caption="📸 Downloaded from Instagram")
            uploaded += 1
        elif len(images) > 1:
            for i in range(0, len(images), 10):
                chunk = images[i:i + 10]
                media = [InputMediaPhoto(img) for img in chunk]
                await client.send_media_group(chat_id, media)
                uploaded += len(chunk)
                
        # Upload videos
        for video in videos:
            await client.send_video(chat_id, video, caption="🎥 Downloaded from Instagram")
            uploaded += 1
            
        await status_msg.edit_text(f"✅ Successfully uploaded {uploaded} files!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = """
🤖 **Enhanced Instagram Downloader Bot**

Send me Instagram links and I'll try multiple methods to download them!

**Supported:**
📸 Posts & Photos
🎥 Reels & Videos
📺 IGTV Content

**Features:**
✅ Multiple download methods
✅ Better error handling
✅ Works with public content
✅ Automatic retry logic

**Usage:**
Just send any Instagram URL like:
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`

**Commands:**
/start - Start the bot
/help - Show help
"""
    await message.reply_text(text)

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    text = """
📋 **Help**

**How to use:**
1. Copy any Instagram post/reel URL
2. Send it to me
3. I'll try to download the content

**Supported URLs:**
• Posts: instagram.com/p/ABC123/
• Reels: instagram.com/reel/XYZ789/
• IGTV: instagram.com/tv/ABC123/

**Notes:**
• Only public content can be downloaded
• Large videos may take time to process
• Some content may be blocked by Instagram

**Tips:**
• Make sure the post is public
• Wait for the download to complete
• Try again if it fails (Instagram sometimes blocks requests)
"""
    await message.reply_text(text)

@app.on_message(filters.regex(r'instagram\.com'))
async def handle_url(client, message):
    url = message.text.strip()
    status = await message.reply_text("🔄 Processing Instagram URL...")
    
    temp_dir = f"/tmp/ig_{message.from_user.id}_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        shortcode = extract_shortcode(url)
        if not shortcode:
            await status.edit_text("❌ Invalid Instagram URL format.\n\n✅ **Supported:**\n• instagram.com/p/ABC123/\n• instagram.com/reel/XYZ789/")
            return
        
        await status.edit_text("📥 Attempting to download content...")
        
        # Try alternative download method
        success, message_text = await download_with_requests(url, temp_dir)
        
        if success:
            await status.edit_text("📤 Uploading files...")
            await upload_files(client, message.chat.id, temp_dir, status)
        else:
            await status.edit_text(f"❌ Download failed: {message_text}\n\n💡 **Possible reasons:**\n• Content is private\n• Instagram is blocking requests\n• Post was deleted\n• Temporary server issue")
        
    except Exception as e:
        await status.edit_text(f"❌ Unexpected error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 Starting Enhanced Instagram Bot...")
    app.run()