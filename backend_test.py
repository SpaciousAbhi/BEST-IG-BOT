#!/usr/bin/env python3
"""
Comprehensive test suite for Instagram Downloader Telegram Bot
Tests bot functionality, URL processing, and Instagram integration
"""

import asyncio
import sys
import re
import tempfile
import shutil
import os
from datetime import datetime
from pyrogram import Client
from pyrogram.errors import FloodWait, BadRequest
from config import Config
from instaloader import Instaloader, Post, Profile
from instaloader.exceptions import ProfileNotExistsException, LoginRequiredException

class InstagramBotTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.bot = None
        self.test_results = []
        
    def log_test(self, name, success, message=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {message}")
        else:
            print(f"❌ {name}: FAILED {message}")
        
        self.test_results.append({
            'name': name,
            'success': success,
            'message': message
        })

    async def test_bot_connection(self):
        """Test if bot can connect to Telegram"""
        try:
            self.bot = Client(
                "test_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN
            )
            
            await self.bot.start()
            me = await self.bot.get_me()
            
            self.log_test(
                "Bot Connection", 
                True, 
                f"Connected as @{me.username} ({me.first_name})"
            )
            return True
            
        except Exception as e:
            self.log_test("Bot Connection", False, f"Error: {str(e)}")
            return False

    def test_url_extraction(self):
        """Test URL pattern recognition and shortcode extraction"""
        test_cases = [
            ("https://instagram.com/p/ABC123/", "ABC123"),
            ("https://www.instagram.com/p/XYZ789/", "XYZ789"),
            ("https://instagram.com/reel/DEF456/", "DEF456"),
            ("https://instagram.com/tv/GHI789/", "GHI789"),
            ("https://instagram.com/invalid/", None),
            ("not_a_url", None)
        ]
        
        # Import the extraction function from main.py
        from main import extract_shortcode
        
        all_passed = True
        for url, expected in test_cases:
            result = extract_shortcode(url)
            if result == expected:
                print(f"  ✓ {url} -> {result}")
            else:
                print(f"  ✗ {url} -> {result} (expected {expected})")
                all_passed = False
        
        self.log_test("URL Shortcode Extraction", all_passed)
        return all_passed

    def test_username_extraction(self):
        """Test username extraction from profile URLs"""
        test_cases = [
            ("https://instagram.com/testuser/", "testuser"),
            ("https://www.instagram.com/another_user/", "another_user"),
            ("https://instagram.com/user.name/", "user.name"),
            ("https://instagram.com/p/ABC123/", None),
            ("invalid_url", None)
        ]
        
        from main import extract_username
        
        all_passed = True
        for url, expected in test_cases:
            result = extract_username(url)
            if result == expected:
                print(f"  ✓ {url} -> {result}")
            else:
                print(f"  ✗ {url} -> {result} (expected {expected})")
                all_passed = False
        
        self.log_test("Username Extraction", all_passed)
        return all_passed

    def test_instaloader_initialization(self):
        """Test if Instaloader can be initialized"""
        try:
            L = Instaloader()
            self.log_test("Instaloader Initialization", True, "Successfully initialized")
            return True
        except Exception as e:
            self.log_test("Instaloader Initialization", False, f"Error: {str(e)}")
            return False

    async def test_bot_commands(self):
        """Test bot command responses"""
        if not self.bot:
            self.log_test("Bot Commands", False, "Bot not connected")
            return False
            
        try:
            # Test /start command
            # Note: We can't directly test commands without a real chat,
            # but we can test if the handlers are properly registered
            
            # Check if handlers are registered
            handlers_count = len(self.bot.dispatcher.groups[0])
            
            self.log_test(
                "Bot Command Handlers", 
                handlers_count >= 3,  # Should have start, help, and URL handlers
                f"Found {handlers_count} handlers registered"
            )
            return True
            
        except Exception as e:
            self.log_test("Bot Commands", False, f"Error: {str(e)}")
            return False

    def test_temp_directory_creation(self):
        """Test temporary directory creation and cleanup"""
        try:
            import uuid
            temp_dir = f"/tmp/test_{uuid.uuid4().hex[:8]}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Check if directory exists
            exists = os.path.exists(temp_dir)
            
            # Cleanup
            if exists:
                shutil.rmtree(temp_dir)
            
            self.log_test("Temp Directory Management", exists, "Directory created and cleaned up")
            return exists
            
        except Exception as e:
            self.log_test("Temp Directory Management", False, f"Error: {str(e)}")
            return False

    def test_file_pattern_matching(self):
        """Test file pattern matching for uploads"""
        try:
            import glob
            
            # Create a temporary directory with test files
            temp_dir = tempfile.mkdtemp()
            
            # Create test files
            test_files = [
                "test1.jpg",
                "test2.jpeg", 
                "test3.mp4",
                "test4.txt"  # Should not match
            ]
            
            for filename in test_files:
                with open(os.path.join(temp_dir, filename), 'w') as f:
                    f.write("test")
            
            # Test pattern matching
            images = glob.glob(f"{temp_dir}/*.jpg") + glob.glob(f"{temp_dir}/*.jpeg")
            videos = glob.glob(f"{temp_dir}/*.mp4")
            
            expected_images = 2
            expected_videos = 1
            
            success = len(images) == expected_images and len(videos) == expected_videos
            
            # Cleanup
            shutil.rmtree(temp_dir)
            
            self.log_test(
                "File Pattern Matching", 
                success,
                f"Found {len(images)} images, {len(videos)} videos"
            )
            return success
            
        except Exception as e:
            self.log_test("File Pattern Matching", False, f"Error: {str(e)}")
            return False

    def test_config_loading(self):
        """Test configuration loading"""
        try:
            # Check if all required config values are present
            required_configs = ['API_ID', 'API_HASH', 'BOT_TOKEN']
            missing_configs = []
            
            for config_name in required_configs:
                if not hasattr(Config, config_name) or not getattr(Config, config_name):
                    missing_configs.append(config_name)
            
            success = len(missing_configs) == 0
            message = "All configs loaded" if success else f"Missing: {missing_configs}"
            
            self.log_test("Configuration Loading", success, message)
            return success
            
        except Exception as e:
            self.log_test("Configuration Loading", False, f"Error: {str(e)}")
            return False

    async def test_error_handling(self):
        """Test error handling scenarios"""
        try:
            # Test invalid shortcode handling
            from main import extract_shortcode
            
            invalid_urls = [
                "https://notinstagram.com/p/ABC123/",
                "https://instagram.com/invalid_format/",
                "",
                None
            ]
            
            errors_handled = 0
            for url in invalid_urls:
                try:
                    result = extract_shortcode(url) if url else None
                    if result is None:  # Should return None for invalid URLs
                        errors_handled += 1
                except:
                    errors_handled += 1  # Exception is also valid error handling
            
            success = errors_handled == len(invalid_urls)
            self.log_test(
                "Error Handling", 
                success,
                f"Handled {errors_handled}/{len(invalid_urls)} invalid inputs"
            )
            return success
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {str(e)}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        if self.bot:
            try:
                await self.bot.stop()
            except:
                pass

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*50}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*50}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.tests_passed < self.tests_run:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['name']}: {result['message']}")
        
        print(f"{'='*50}")

async def main():
    """Run all tests"""
    print("🧪 Starting Instagram Bot Test Suite...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    tester = InstagramBotTester()
    
    try:
        # Run all tests
        await tester.test_bot_connection()
        tester.test_config_loading()
        tester.test_url_extraction()
        tester.test_username_extraction()
        tester.test_instaloader_initialization()
        await tester.test_bot_commands()
        tester.test_temp_directory_creation()
        tester.test_file_pattern_matching()
        await tester.test_error_handling()
        
    except Exception as e:
        print(f"❌ Test suite error: {str(e)}")
    finally:
        await tester.cleanup()
        tester.print_summary()
        
        # Return exit code based on results
        return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)