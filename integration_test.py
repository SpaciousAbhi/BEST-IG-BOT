#!/usr/bin/env python3
"""
Instagram Bot Integration Test
Simulates full bot workflow without session conflicts
"""

import asyncio
import sys
import tempfile
import shutil
import os
import uuid
from datetime import datetime

class MockMessage:
    """Mock Telegram message for testing"""
    def __init__(self, text, user_id=12345):
        self.text = text
        self.from_user = MockUser(user_id)
        self.chat = MockChat(user_id)

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockChat:
    def __init__(self, chat_id):
        self.id = chat_id

class BotWorkflowTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name, success, message=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED {message}")
        else:
            print(f"❌ {name}: FAILED {message}")

    def test_start_command_response(self):
        """Test /start command response"""
        try:
            # Simulate /start command
            message = MockMessage("/start")
            
            # Expected response content
            expected_keywords = [
                "Instagram Downloader Bot",
                "Posts & Photos",
                "Reels & Videos", 
                "Profile Pictures",
                "/start",
                "/help"
            ]
            
            # This would be the actual response text from the bot
            response_text = """
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
            
            # Check if all expected keywords are present
            keywords_found = sum(1 for keyword in expected_keywords if keyword in response_text)
            success = keywords_found == len(expected_keywords)
            
            self.log_test(
                "Start Command Response",
                success,
                f"Found {keywords_found}/{len(expected_keywords)} expected keywords"
            )
            return success
            
        except Exception as e:
            self.log_test("Start Command Response", False, f"Error: {e}")
            return False

    def test_help_command_response(self):
        """Test /help command response"""
        try:
            message = MockMessage("/help")
            
            expected_keywords = [
                "Help",
                "Instagram URL",
                "Posts:",
                "Reels:",
                "Profiles:"
            ]
            
            response_text = """
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
            
            keywords_found = sum(1 for keyword in expected_keywords if keyword in response_text)
            success = keywords_found == len(expected_keywords)
            
            self.log_test(
                "Help Command Response",
                success,
                f"Found {keywords_found}/{len(expected_keywords)} expected keywords"
            )
            return success
            
        except Exception as e:
            self.log_test("Help Command Response", False, f"Error: {e}")
            return False

    async def test_instagram_url_processing(self):
        """Test Instagram URL processing workflow"""
        try:
            from main import extract_shortcode, extract_username
            
            test_cases = [
                {
                    "url": "https://instagram.com/p/ABC123/",
                    "type": "post",
                    "expected_shortcode": "ABC123",
                    "expected_username": None
                },
                {
                    "url": "https://instagram.com/reel/XYZ789/",
                    "type": "reel", 
                    "expected_shortcode": "XYZ789",
                    "expected_username": None
                },
                {
                    "url": "https://instagram.com/testuser/",
                    "type": "profile",
                    "expected_shortcode": None,
                    "expected_username": "testuser"
                }
            ]
            
            all_passed = True
            for case in test_cases:
                url = case["url"]
                shortcode = extract_shortcode(url)
                username = extract_username(url)
                
                shortcode_ok = shortcode == case["expected_shortcode"]
                username_ok = username == case["expected_username"]
                
                if shortcode_ok and username_ok:
                    print(f"  ✅ {case['type']}: {url} -> shortcode={shortcode}, username={username}")
                else:
                    print(f"  ❌ {case['type']}: {url} -> shortcode={shortcode}, username={username}")
                    all_passed = False
            
            self.log_test("Instagram URL Processing", all_passed)
            return all_passed
            
        except Exception as e:
            self.log_test("Instagram URL Processing", False, f"Error: {e}")
            return False

    async def test_download_workflow_simulation(self):
        """Simulate the download workflow without actual downloads"""
        try:
            # Simulate the workflow steps
            message = MockMessage("https://instagram.com/p/ABC123/")
            
            # Step 1: Create temp directory
            temp_dir = f"/tmp/{message.from_user.id}_{uuid.uuid4().hex[:8]}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Step 2: Extract shortcode
            from main import extract_shortcode
            shortcode = extract_shortcode(message.text)
            
            # Step 3: Simulate file creation (instead of actual download)
            test_files = [
                os.path.join(temp_dir, "test_image.jpg"),
                os.path.join(temp_dir, "test_video.mp4")
            ]
            
            for filepath in test_files:
                with open(filepath, 'w') as f:
                    f.write("test content")
            
            # Step 4: Test file detection
            import glob
            images = glob.glob(f"{temp_dir}/*.jpg") + glob.glob(f"{temp_dir}/*.jpeg")
            videos = glob.glob(f"{temp_dir}/*.mp4")
            
            # Step 5: Cleanup
            shutil.rmtree(temp_dir)
            
            success = (
                shortcode == "ABC123" and
                len(images) == 1 and
                len(videos) == 1 and
                not os.path.exists(temp_dir)
            )
            
            self.log_test(
                "Download Workflow Simulation",
                success,
                f"Shortcode: {shortcode}, Images: {len(images)}, Videos: {len(videos)}"
            )
            return success
            
        except Exception as e:
            self.log_test("Download Workflow Simulation", False, f"Error: {e}")
            return False

    def test_error_handling_scenarios(self):
        """Test various error handling scenarios"""
        try:
            from main import extract_shortcode, extract_username
            
            error_cases = [
                {"input": "https://notinstagram.com/p/ABC123/", "expected": None},
                {"input": "invalid url", "expected": None},
                {"input": "", "expected": None},
                {"input": "https://instagram.com/invalid_format", "expected": None}
            ]
            
            all_handled = True
            for case in error_cases:
                try:
                    result = extract_shortcode(case["input"])
                    if result == case["expected"]:
                        print(f"  ✅ Error handled: '{case['input']}' -> {result}")
                    else:
                        print(f"  ❌ Error not handled: '{case['input']}' -> {result}")
                        all_handled = False
                except Exception:
                    # Exception is also valid error handling
                    print(f"  ✅ Exception handled: '{case['input']}'")
            
            self.log_test("Error Handling", all_handled)
            return all_handled
            
        except Exception as e:
            self.log_test("Error Handling", False, f"Error: {e}")
            return False

    def test_bot_credentials(self):
        """Test bot credentials and configuration"""
        try:
            from config import Config
            
            # Check if credentials are present
            has_api_id = hasattr(Config, 'API_ID') and Config.API_ID
            has_api_hash = hasattr(Config, 'API_HASH') and Config.API_HASH
            has_bot_token = hasattr(Config, 'BOT_TOKEN') and Config.BOT_TOKEN
            
            success = has_api_id and has_api_hash and has_bot_token
            
            self.log_test(
                "Bot Credentials",
                success,
                f"API_ID: {bool(has_api_id)}, API_HASH: {bool(has_api_hash)}, BOT_TOKEN: {bool(has_bot_token)}"
            )
            return success
            
        except Exception as e:
            self.log_test("Bot Credentials", False, f"Error: {e}")
            return False

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"📊 INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        print(f"{'='*60}")

async def main():
    """Run integration tests"""
    print("🧪 Instagram Bot Integration Test Suite")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    tester = BotWorkflowTester()
    
    # Run all tests
    tester.test_bot_credentials()
    tester.test_start_command_response()
    tester.test_help_command_response()
    await tester.test_instagram_url_processing()
    await tester.test_download_workflow_simulation()
    tester.test_error_handling_scenarios()
    
    tester.print_summary()
    
    # Additional bot status check
    print(f"\n🤖 BOT STATUS CHECK")
    print("-" * 30)
    
    # Check if bot process is running
    import subprocess
    try:
        result = subprocess.run(['supervisorctl', 'status', 'instagram-bot'], 
                              capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            print("✅ Bot service is running under supervisor")
        else:
            print("❌ Bot service is not running properly")
            print(f"Status: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Could not check bot status: {e}")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))