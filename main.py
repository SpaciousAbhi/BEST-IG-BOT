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

async def download_with_retry(post, temp_dir, max_retries=3):
    """Download post with retry logic and better error handling"""
    for attempt in range(max_retries):
        try:
            L.download_post(post, temp_dir)
            return True
        except ConnectionException as e:
            if "401 Unauthorized" in str(e) or "429" in str(e):
                print(f"Rate limited or unauthorized, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return False
            elif "Please wait" in str(e):
                print(f"Instagram rate limit, waiting... Attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(10)  # Wait longer for rate limits
                    continue
                return False
            else:
                print(f"Connection error: {e}")
                return False
        except Exception as e:
            print(f"Download error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            return False
    return False

async def download_profile_pic_with_retry(profile, temp_dir, max_retries=3):
    """Download profile picture with retry logic"""
    for attempt in range(max_retries):
        try:
            L.download_profilepic(profile, temp_dir)
            return True
        except Exception as e:
            print(f"Profile pic download error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            return False
    return False

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
    session_status = "🔓 Logged in" if session_loaded else "🔒 Login required for private content"
    text = f"""
🤖 **Instagram Downloader Bot**

{session_status}

Send me Instagram links and I'll download them for you!

**Supported:**
📸 Posts & Photos
🎥 Reels & Videos  
🖼️ Profile Pictures
📚 Stories (requires login)
🎯 IGTV Videos

**Usage:**
Just send any Instagram URL like:
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`
• `https://instagram.com/username/` (for profile pic)

**Commands:**
/start - Start the bot
/help - Show help
/login - Login to Instagram (owner only)
/status - Check login status
"""
    await message.reply_text(text)

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    text = """
📋 **Help**

**How to use:**
1. Send me any Instagram URL
2. I'll try to download it automatically
3. For private content, login may be required

**Supported URLs:**
• Posts: instagram.com/p/ABC123/
• Reels: instagram.com/reel/XYZ789/
• IGTV: instagram.com/tv/ABC123/
• Profiles: instagram.com/username/ (downloads profile picture)

**Notes:**
• Some content may require Instagram login
• Rate limits may apply
• Large videos may take time to process

**Commands:**
/start - Start the bot
/help - Show this help
/status - Check Instagram login status
"""
    await message.reply_text(text)

@app.on_message(filters.command("status"))
async def status_cmd(client, message):
    if session_loaded:
        text = "🔓 **Status: Logged in to Instagram**\n\nCan download both public and private content."
    else:
        text = "🔒 **Status: Not logged in**\n\nCan only download public content. Some downloads may fail due to Instagram restrictions."
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