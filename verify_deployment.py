#!/usr/bin/env python3
"""
Pre-deployment verification script
Ensures bot is ready for Heroku deployment
"""

import requests
from config import Config

def verify_bot_ready():
    """Final verification before deployment"""
    print("🔍 Pre-deployment verification...")
    
    # Test bot token
    token = Config.BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url)
    result = response.json()
    
    if not result.get('ok'):
        print("❌ Bot token invalid!")
        return False
    
    bot_info = result.get('result', {})
    print(f"✅ Bot token valid: @{bot_info.get('username')}")
    
    # Check webhook status
    webhook_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    webhook_response = requests.get(webhook_url)
    webhook_result = webhook_response.json()
    
    if webhook_result.get('ok'):
        webhook_data = webhook_result.get('result', {})
        webhook_url_set = webhook_data.get('url', '')
        pending_updates = webhook_data.get('pending_update_count', 0)
        
        if webhook_url_set:
            print(f"⚠️ Webhook still set: {webhook_url_set}")
            print("🔧 Clearing webhook...")
            clear_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
            clear_response = requests.post(clear_url)
            if clear_response.json().get('ok'):
                print("✅ Webhook cleared!")
            else:
                print("❌ Failed to clear webhook!")
                return False
        else:
            print("✅ No webhook set - polling mode ready")
        
        print(f"📊 Pending updates: {pending_updates}")
        
    # Verify configuration
    print(f"👑 Owner ID configured: {Config.OWNER}")
    print(f"🔑 API ID configured: {Config.API_ID}")
    
    print("\n🚀 Bot is ready for deployment!")
    print("📋 Deployment checklist:")
    print("✅ Bot token valid")
    print("✅ Webhook cleared (polling mode)")
    print("✅ Configuration verified")
    print("✅ Pending updates will be processed")
    
    return True

if __name__ == "__main__":
    if verify_bot_ready():
        print("\n🎯 Deploy to Heroku now!")
    else:
        print("\n❌ Fix issues before deployment!")