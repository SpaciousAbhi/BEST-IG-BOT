"""
Simple Instagram Bot with proper time handling
"""
import os
import time
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.errors import BadMsgNotification
from config import Config

# Simple bot instance
app = Client(
    "instagram_bot",  # Use a session name instead of :memory:
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workdir="/tmp"  # Use /tmp for session files
)

@app.on_message(filters.command("start"))
async def start_command(client, message):
    await message.reply_text("""
🤖 **Instagram Downloader Bot**

I can download Instagram content for you!

**Supported:**
📸 Posts & Photos
🎥 Reels & Videos  
🖼️ Profile Pictures

**Usage:**
Just send any Instagram URL like:
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`
• `https://instagram.com/username/` (for profile pic)

Send me an Instagram URL to test! 🚀
""")

@app.on_message(filters.command("help"))
async def help_command(client, message):
    await message.reply_text("""
📋 **Help**

**How to use:**
1. Send me any Instagram URL
2. I'll try to download it automatically

**Supported URLs:**
• Posts: instagram.com/p/ABC123/
• Reels: instagram.com/reel/XYZ789/
• Profiles: instagram.com/username/

**Note:** Some content may require special handling.
""")

@app.on_message(filters.regex(r'instagram\.com'))
async def handle_instagram_url(client, message):
    url = message.text.strip()
    await message.reply_text(f"🔄 Processing Instagram URL: {url}\n\n⏳ This feature is being enhanced...")

async def main():
    print("🚀 Starting Simple Instagram Bot...")
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            print(f"📡 Connection attempt {attempt + 1}...")
            await app.start()
            print("✅ Bot connected successfully!")
            print("🎯 Bot is ready to receive messages!")
            print("Press Ctrl+C to stop the bot")
            await idle()
            break
        except BadMsgNotification as e:
            print(f"⚠️ Time sync error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print("⏰ Waiting 5 seconds before retry...")
                await asyncio.sleep(5)
            else:
                print("❌ Failed after all retries. Check system time.")
                raise
        except Exception as e:
            print(f"❌ Connection error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            else:
                raise
    
    await app.stop()

if __name__ == "__main__":
    asyncio.run(main())