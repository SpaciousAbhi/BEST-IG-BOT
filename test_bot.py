"""
Simple test bot to verify credentials
"""

from pyrogram import Client
from config import Config
import asyncio

async def test_bot():
    bot = Client(
        "TestBot",
        bot_token=Config.BOT_TOKEN,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
    )
    
    try:
        await bot.start()
        print("✅ Bot connected successfully!")
        me = await bot.get_me()
        print(f"Bot username: @{me.username}")
        print(f"Bot name: {me.first_name}")
        await bot.stop()
        return True
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    print(f"Test result: {'PASSED' if result else 'FAILED'}")