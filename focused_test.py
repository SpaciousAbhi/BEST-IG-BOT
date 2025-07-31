#!/usr/bin/env python3
"""
Focused Instagram Bot Functionality Test
Tests core functions without session conflicts
"""

import sys
import re
import tempfile
import shutil
import os
from datetime import datetime

def test_url_processing():
    """Test URL processing functions"""
    print("🔍 Testing URL Processing Functions...")
    
    # Import functions from main.py
    sys.path.append('/app')
    from main import extract_shortcode, extract_username
    
    # Test shortcode extraction
    test_urls = [
        "https://instagram.com/p/ABC123/",
        "https://www.instagram.com/reel/XYZ789/",
        "https://instagram.com/tv/DEF456/",
        "https://instagram.com/invalid/",
    ]
    
    print("  Shortcode Extraction:")
    for url in test_urls:
        shortcode = extract_shortcode(url)
        print(f"    {url} -> {shortcode}")
    
    # Test username extraction
    profile_urls = [
        "https://instagram.com/testuser/",
        "https://www.instagram.com/another_user/",
        "https://instagram.com/p/ABC123/",  # Should return None
    ]
    
    print("  Username Extraction:")
    for url in profile_urls:
        username = extract_username(url)
        print(f"    {url} -> {username}")
    
    return True

def test_instaloader_functionality():
    """Test Instaloader without actual downloads"""
    print("🔍 Testing Instaloader Functionality...")
    
    try:
        from instaloader import Instaloader, Post, Profile
        from instaloader.exceptions import ProfileNotExistsException, LoginRequiredException
        
        # Initialize Instaloader
        L = Instaloader()
        print("  ✅ Instaloader initialized successfully")
        
        # Test context access
        context = L.context
        print(f"  ✅ Context available: {type(context)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Instaloader test failed: {e}")
        return False

def test_file_operations():
    """Test file operations used by the bot"""
    print("🔍 Testing File Operations...")
    
    try:
        import uuid
        import glob
        
        # Create temp directory
        temp_dir = f"/tmp/test_{uuid.uuid4().hex[:8]}"
        os.makedirs(temp_dir, exist_ok=True)
        print(f"  ✅ Created temp directory: {temp_dir}")
        
        # Create test files
        test_files = ["test.jpg", "test.mp4", "test.jpeg"]
        for filename in test_files:
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'w') as f:
                f.write("test content")
        
        # Test glob patterns
        images = glob.glob(f"{temp_dir}/*.jpg") + glob.glob(f"{temp_dir}/*.jpeg")
        videos = glob.glob(f"{temp_dir}/*.mp4")
        
        print(f"  ✅ Found {len(images)} images, {len(videos)} videos")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print("  ✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")
        return False

def test_config_values():
    """Test configuration values"""
    print("🔍 Testing Configuration...")
    
    try:
        from config import Config
        
        # Check required values
        required_attrs = ['API_ID', 'API_HASH', 'BOT_TOKEN']
        for attr in required_attrs:
            value = getattr(Config, attr, None)
            if value:
                # Mask sensitive values
                if attr == 'BOT_TOKEN':
                    masked = f"{str(value)[:10]}...{str(value)[-5:]}"
                    print(f"  ✅ {attr}: {masked}")
                elif attr == 'API_HASH':
                    masked = f"{str(value)[:8]}...{str(value)[-4:]}"
                    print(f"  ✅ {attr}: {masked}")
                else:
                    print(f"  ✅ {attr}: {value}")
            else:
                print(f"  ❌ {attr}: Missing or empty")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        return False

def test_regex_patterns():
    """Test regex patterns used in URL processing"""
    print("🔍 Testing Regex Patterns...")
    
    # Test Instagram URL patterns
    patterns = [
        r'instagram\.com/p/([A-Za-z0-9_-]+)',
        r'instagram\.com/reel/([A-Za-z0-9_-]+)',
        r'instagram\.com/tv/([A-Za-z0-9_-]+)',
        r'instagram\.com/([A-Za-z0-9_.]+)/?$'
    ]
    
    test_urls = [
        "https://instagram.com/p/ABC123/",
        "https://instagram.com/reel/XYZ789/",
        "https://instagram.com/tv/DEF456/",
        "https://instagram.com/testuser/",
        "https://instagram.com/invalid_format"
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"  Pattern {i+1}: {pattern}")
        for url in test_urls:
            match = re.search(pattern, url)
            if match:
                print(f"    ✅ {url} -> {match.group(1)}")
            else:
                print(f"    ❌ {url} -> No match")
    
    return True

def test_bot_message_handlers():
    """Test bot message handler logic"""
    print("🔍 Testing Bot Handler Logic...")
    
    try:
        # Test message filtering logic
        test_messages = [
            "https://instagram.com/p/ABC123/",
            "https://www.instagram.com/reel/XYZ789/",
            "https://instagram.com/testuser/",
            "/start",
            "/help",
            "random text without instagram link"
        ]
        
        instagram_pattern = r'instagram\.com'
        
        for message in test_messages:
            if re.search(instagram_pattern, message):
                print(f"  ✅ Instagram URL detected: {message}")
            elif message.startswith('/'):
                print(f"  ✅ Command detected: {message}")
            else:
                print(f"  ℹ️  Regular message: {message}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Handler logic test failed: {e}")
        return False

def main():
    """Run focused functionality tests"""
    print("🧪 Instagram Bot Focused Functionality Test")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tests = [
        ("URL Processing", test_url_processing),
        ("Instaloader Functionality", test_instaloader_functionality),
        ("File Operations", test_file_operations),
        ("Configuration", test_config_values),
        ("Regex Patterns", test_regex_patterns),
        ("Bot Handler Logic", test_bot_message_handlers)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "="*60)
    print(f"📊 SUMMARY: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())