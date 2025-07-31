#!/usr/bin/env python3
"""
Simple script to clear webhooks and test bot connectivity
"""
import requests
import os
from config import Config

def clear_webhook():
    """Clear Telegram webhook using bot API"""
    try:
        token = Config.BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        
        response = requests.post(url)
        result = response.json()
        
        if result.get('ok'):
            print("✅ Webhook cleared successfully!")
            print(f"📊 Result: {result.get('description', 'Success')}")
        else:
            print(f"❌ Failed to clear webhook: {result}")
            
        # Get webhook info
        info_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        info_response = requests.get(info_url)
        webhook_info = info_response.json()
        
        if webhook_info.get('ok'):
            webhook_data = webhook_info.get('result', {})
            print(f"📋 Current webhook URL: {webhook_data.get('url', 'None')}")
            print(f"📋 Pending updates: {webhook_data.get('pending_update_count', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Error clearing webhook: {e}")
        return False

def test_bot():
    """Test bot credentials"""
    try:
        token = Config.BOT_TOKEN
        url = f"https://api.telegram.org/bot{token}/getMe"
        
        response = requests.get(url)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            print("✅ Bot credentials valid!")
            print(f"🤖 Bot name: {bot_info.get('first_name')}")
            print(f"🤖 Bot username: @{bot_info.get('username')}")
            return True
        else:
            print(f"❌ Invalid bot credentials: {result}")
            return False
    except Exception as e:
        print(f"❌ Error testing bot: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing bot setup...")
    
    if test_bot():
        clear_webhook()
        print("\n🚀 Ready to start bot in polling mode!")
    else:
        print("\n❌ Fix bot credentials first!")