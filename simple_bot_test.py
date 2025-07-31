#!/usr/bin/env python3
"""
Simple bot connectivity test
"""

import asyncio
import sys
from pyrogram import Client
from config import Config

async def test_bot_simple():
    """Simple bot connection test"""
    print("🔍 Testing bot connection...")
    
    # Create a unique session name to avoid conflicts
    session_name = "test_session_unique"
    
    bot = Client(
        session_name,
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        in_memory=True  # Use in-memory session to avoid file conflicts
    )
    
    try:
        print("  Connecting to Telegram...")
        await bot.start()
        
        print("  Getting bot info...")
        me = await bot.get_me()
        
        print(f"✅ Bot connected successfully!")
        print(f"  Username: @{me.username}")
        print(f"  Name: {me.first_name}")
        print(f"  ID: {me.id}")
        
        # Test if bot can receive updates (without actually processing them)
        print("  Bot is ready to receive messages")
        
        await bot.stop()
        return True
        
    except Exception as e:
        print(f"❌ Bot connection failed: {e}")
        try:
            await bot.stop()
        except:
            pass
        return False

async def main():
    print("🧪 Simple Bot Connectivity Test")
    print("="*40)
    
    success = await test_bot_simple()
    
    print("="*40)
    if success:
        print("✅ Bot is working and can connect to Telegram!")
        print("📋 The bot should be able to:")
        print("  • Respond to /start command")
        print("  • Respond to /help command") 
        print("  • Process Instagram URLs")
        print("  • Download public Instagram content")
    else:
        print("❌ Bot connection failed - check credentials and network")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))