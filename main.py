"""
Instagram Content Downloader Bot - Enhanced Version with Authentication
Downloads Instagram content from URLs sent by users
"""

import os
import re
import asyncio
import tempfile
import shutil
import glob
import uuid
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait
from config import Config
from instaloader import Instaloader, Profile, Post
from instaloader.exceptions import ProfileNotExistsException, LoginRequiredException, ConnectionException
import time

# Bot instance with in-memory session to avoid lock issues
app = Client(
    ":memory:",  # Use in-memory session to avoid file locks
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Global instances
L = Instaloader(
    download_pictures=True,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    dirname_pattern="{target}",
    filename_pattern="{date_utc}_UTC"
)

# Try to load session if available
session_loaded = False

def load_instagram_session():
    """Load Instagram session from environment or file"""
    global session_loaded
    if session_loaded:
        return True
        
    # Try to load from environment variable (Heroku)
    session_file_id = Config.INSTA_SESSIONFILE_ID
    if session_file_id and Config.USER:
        try:
            # In production, you'd download the session file using the file_id
            # For now, we'll try to load from local file
            if os.path.exists(Config.USER):
                L.load_session_from_file(Config.USER)
                print(f"✅ Instagram session loaded for {Config.USER}")
                session_loaded = True
                return True
        except Exception as e:
            print(f"❌ Failed to load session: {e}")
    
    # Try to login with username if provided but no session
    if Config.USER and not session_loaded:
        print(f"⚠️ No session found for {Config.USER}. Authentication required for some content.")
    
    return session_loaded

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
            await client.send_photo(chat_id, images[0])
            uploaded += 1
        elif len(images) > 1:
            for i in range(0, len(images), 10):
                chunk = images[i:i + 10]
                media = [InputMediaPhoto(img) for img in chunk]
                await client.send_media_group(chat_id, media)
                uploaded += len(chunk)
                
        # Upload videos
        for video in videos:
            await client.send_video(chat_id, video)
            uploaded += 1
            
        await status_msg.edit_text(f"✅ Uploaded {uploaded} files successfully!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = """
🤖 **Instagram Downloader Bot**

Send me Instagram links and I'll download them for you!

**Supported:**
📸 Posts & Photos
🎥 Reels & Videos
🖼️ Profile Pictures

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

1. Send me any Instagram URL
2. I'll download it automatically
3. For private content, login may be required

**Supported URLs:**
• Posts: instagram.com/p/ABC123/
• Reels: instagram.com/reel/XYZ789/
• Profiles: instagram.com/username/

Just paste the link and I'll handle the rest!
"""
    await message.reply_text(text)

@app.on_message(filters.regex(r'instagram\.com'))
async def handle_url(client, message):
    url = message.text.strip()
    status = await message.reply_text("🔄 Processing...")
    
    temp_dir = f"/tmp/{message.from_user.id}_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Try to extract shortcode for posts/reels
        shortcode = extract_shortcode(url)
        if shortcode:
            await status.edit_text("📥 Downloading post/reel...")
            try:
                post = Post.from_shortcode(L.context, shortcode)
                L.download_post(post, temp_dir)
                await upload_files(client, message.chat.id, temp_dir, status)
                return
            except Exception as e:
                await status.edit_text(f"❌ Download failed: {str(e)}")
                return
        
        # Try to extract username for profile
        username = extract_username(url)
        if username:
            await status.edit_text("📥 Downloading profile picture...")
            try:
                profile = Profile.from_username(L.context, username)
                L.download_profilepic(profile, temp_dir)
                await upload_files(client, message.chat.id, temp_dir, status)
                return
            except Exception as e:
                await status.edit_text(f"❌ Download failed: {str(e)}")
                return
                
        await status.edit_text("❌ Invalid Instagram URL or unsupported content type.")
        
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 Starting Instagram Bot...")
    app.run()