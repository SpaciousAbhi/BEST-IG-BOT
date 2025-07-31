"""
Instagram Content Downloader Bot
Downloads Instagram content from URLs sent by users
Supports both public and private content
"""

from pyrogram import Client, idle
from pyromod import listen
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from config import Config
import asyncio
import os
import re
import tempfile
import shutil
from instaloader import Instaloader, Profile, Post, Reel, StoryItem
from instaloader.exceptions import ProfileNotExistsException, LoginRequiredException
from utils import download_and_upload_content
import uuid

# Initialize bot
bot = Client(
    "InstagramBot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    workers=50
)

# Global instaloader instance
L = Instaloader()

# Store user sessions
user_sessions = {}

def extract_instagram_info(url):
    """Extract Instagram URL type and identifier"""
    patterns = {
        'post': r'instagram\.com/p/([A-Za-z0-9_-]+)',
        'reel': r'instagram\.com/reel/([A-Za-z0-9_-]+)', 
        'story': r'instagram\.com/stories/([^/]+)/([0-9]+)',
        'profile': r'instagram\.com/([A-Za-z0-9_.]+)/?$',
        'highlights': r'instagram\.com/stories/highlights/([0-9]+)'
    }
    
    for content_type, pattern in patterns.items():
        match = re.search(pattern, url)
        if match:
            if content_type == 'story':
                return content_type, match.group(1), match.group(2)
            return content_type, match.group(1), None
    
    return None, None, None

async def try_download_without_login(url, user_id):
    """Try to download content without login first"""
    temp_loader = Instaloader()
    temp_dir = f"/tmp/{user_id}_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        content_type, identifier, story_id = extract_instagram_info(url)
        
        if content_type == 'post':
            post = Post.from_shortcode(temp_loader.context, identifier)
            temp_loader.download_post(post, temp_dir)
            return temp_dir, "post"
            
        elif content_type == 'reel':
            post = Post.from_shortcode(temp_loader.context, identifier)
            temp_loader.download_post(post, temp_dir)
            return temp_dir, "reel"
            
        elif content_type == 'profile':
            profile = Profile.from_username(temp_loader.context, identifier)
            # Download profile picture
            temp_loader.download_profilepic(profile, temp_dir)
            return temp_dir, "profile_pic"
            
        return None, None
        
    except Exception as e:
        print(f"Error downloading without login: {e}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None, None

@bot.on_message(filters.command("start"))
async def start_command(client, message):
    welcome_text = """
🤖 **Instagram Content Downloader Bot**

Send me any Instagram link and I'll download it for you!

**Supported Content:**
📸 Posts & Photos
🎥 Reels & Videos  
📖 Stories (if public)
🖼️ Profile Pictures
✨ Highlights (if public)

**How to use:**
Just send me an Instagram URL like:
`https://instagram.com/p/ABC123/`
`https://instagram.com/reel/XYZ789/`

For **private content**, I'll ask you to login when needed.

**Commands:**
/start - Show this message
/help - Get help
/login - Login to your Instagram account
/logout - Logout from your account
"""
    
    await message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 How to Get Instagram Links", callback_data="how_to_links")],
            [InlineKeyboardButton("🔐 Privacy & Security", callback_data="privacy_info")]
        ])
    )

@bot.on_message(filters.command("help"))
async def help_command(client, message):
    help_text = """
📋 **How to use this bot:**

1️⃣ **Send Instagram URL**
   Just paste any Instagram link

2️⃣ **Public Content** 
   Downloads automatically without login

3️⃣ **Private Content**
   I'll ask you to login when needed

**Supported URLs:**
• Posts: `instagram.com/p/ABC123/`
• Reels: `instagram.com/reel/XYZ789/` 
• Stories: `instagram.com/stories/username/123456/`
• Profile Pics: `instagram.com/username/`

**Commands:**
/login - Login to access private content
/logout - Logout from your account
/status - Check your login status
"""
    await message.reply_text(help_text)

@bot.on_message(filters.command("login"))
async def login_command(client, message):
    if message.from_user.id in user_sessions:
        await message.reply_text("✅ You're already logged in! Use /logout to logout first.")
        return
        
    try:
        username = await client.ask(
            message.chat.id,
            "📝 Please enter your Instagram username:",
            filters=filters.text,
            timeout=60
        )
        
        password = await client.ask(
            message.chat.id, 
            "🔐 Please enter your Instagram password:\n\n⚠️ Your credentials are not saved permanently.",
            filters=filters.text,
            timeout=60
        )
        
        # Create user-specific loader
        user_loader = Instaloader()
        
        status_msg = await message.reply_text("🔄 Logging you in...")
        
        try:
            user_loader.login(username.text, password.text)
            user_sessions[message.from_user.id] = user_loader
            
            await status_msg.edit_text("✅ Successfully logged in! You can now access private content.")
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Login failed: {str(e)}\n\nPlease try again with /login")
            
    except asyncio.TimeoutError:
        await message.reply_text("⏱️ Login timeout. Please try again with /login")

@bot.on_message(filters.command("logout")) 
async def logout_command(client, message):
    if message.from_user.id in user_sessions:
        del user_sessions[message.from_user.id]
        await message.reply_text("✅ Successfully logged out!")
    else:
        await message.reply_text("❌ You're not logged in.")

@bot.on_message(filters.command("status"))
async def status_command(client, message):
    if message.from_user.id in user_sessions:
        await message.reply_text("✅ You're logged in and can access private content.")
    else:
        await message.reply_text("❌ You're not logged in. Use /login to access private content.")

@bot.on_message(filters.regex(r'instagram\.com'))
async def handle_instagram_url(client, message):
    url = message.text.strip()
    user_id = message.from_user.id
    
    status_msg = await message.reply_text("🔄 Processing your Instagram link...")
    
    # First try without login
    temp_dir, content_type = await try_download_without_login(url, user_id)
    
    if temp_dir and content_type:
        await status_msg.edit_text("📤 Uploading content...")
        await download_and_upload_content(client, message.chat.id, temp_dir, status_msg)
        return
    
    # If failed, check if user is logged in
    if user_id not in user_sessions:
        await status_msg.edit_text(
            "🔐 This content requires login to access.\n\nUse /login to authenticate with your Instagram account.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔑 Login Now", callback_data="login_prompt")]
            ])
        )
        return
    
    # Try with user's session
    await status_msg.edit_text("🔄 Downloading with your account...")
    
    user_loader = user_sessions[user_id]
    temp_dir = f"/tmp/{user_id}_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        content_type, identifier, story_id = extract_instagram_info(url)
        
        if content_type == 'post':
            post = Post.from_shortcode(user_loader.context, identifier)
            user_loader.download_post(post, temp_dir)
            
        elif content_type == 'reel':
            post = Post.from_shortcode(user_loader.context, identifier)
            user_loader.download_post(post, temp_dir)
            
        elif content_type == 'story':
            profile = Profile.from_username(user_loader.context, identifier)
            # Note: Stories might be expired, this is a simplified implementation
            user_loader.download_stories(profile, temp_dir)
            
        elif content_type == 'profile':
            profile = Profile.from_username(user_loader.context, identifier)
            user_loader.download_profilepic(profile, temp_dir)
            
        await status_msg.edit_text("📤 Uploading content...")
        await download_and_upload_content(client, message.chat.id, temp_dir, status_msg)
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Failed to download: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@bot.on_callback_query()
async def handle_callbacks(client, callback_query):
    data = callback_query.data
    
    if data == "login_prompt":
        await callback_query.message.reply_text("Use /login command to authenticate with your Instagram account.")
        await callback_query.answer()
        
    elif data == "how_to_links":
        await callback_query.message.reply_text(
            "📱 **How to get Instagram links:**\n\n"
            "1. Open Instagram app/website\n"
            "2. Go to the post/reel you want\n" 
            "3. Tap the 3 dots menu\n"
            "4. Select 'Copy Link'\n"
            "5. Send the link to me!\n\n"
            "**Example links:**\n"
            "`https://instagram.com/p/ABC123/`\n"
            "`https://instagram.com/reel/XYZ789/`"
        )
        await callback_query.answer()
        
    elif data == "privacy_info":
        await callback_query.message.reply_text(
            "🔐 **Privacy & Security:**\n\n"
            "• Your Instagram credentials are only used for downloading\n"
            "• Login sessions are temporary and not permanently stored\n"
            "• No data is shared with third parties\n"
            "• You can logout anytime with /logout\n\n"
            "⚠️ Only login if you trust this bot with your Instagram access."
        )
        await callback_query.answer()

if __name__ == "__main__":
    print("🤖 Starting Instagram Bot...")
    bot.start()
    print("✅ Bot is running!")
    idle()
    bot.stop()