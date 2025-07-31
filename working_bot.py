"""
Working Instagram Content Downloader
Uses Instagram's oEmbed API and improved scraping methods
"""

import os
import re
import asyncio
import tempfile
import shutil
import glob
import uuid
import requests
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from config import Config
import time
from urllib.parse import quote

# Bot instance
app = Client(
    ":memory:",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

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

async def get_instagram_info(url):
    """Get Instagram post info using oEmbed API"""
    try:
        oembed_url = f"https://api.instagram.com/oembed/?url={quote(url)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(oembed_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"oEmbed API returned {response.status_code}"
            
    except Exception as e:
        return False, f"oEmbed error: {str(e)}"

async def download_instagram_content(url, temp_dir):
    """Download Instagram content using multiple methods"""
    try:
        shortcode = extract_shortcode(url)
        if not shortcode:
            return False, "Invalid URL format"
        
        # Method 1: Try oEmbed API first
        success, oembed_data = await get_instagram_info(url)
        if success and isinstance(oembed_data, dict):
            title = oembed_data.get('title', 'Instagram Post')
            author = oembed_data.get('author_name', 'Unknown')
            print(f"Found post: {title} by {author}")
        
        # Method 2: Try direct page scraping with better headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        page_url = f"https://www.instagram.com/p/{shortcode}/"
        response = requests.get(page_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            # Try with different URL format
            page_url = f"https://www.instagram.com/reel/{shortcode}/"
            response = requests.get(page_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            content = response.text
            
            # Look for JSON data in script tags
            json_pattern = r'window\._sharedData\s*=\s*({.*?});'
            json_match = re.search(json_pattern, content)
            
            downloaded_files = []
            
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    # Extract media from the shared data
                    entry_data = data.get('entry_data', {})
                    posts = entry_data.get('PostPage', [])
                    
                    if posts:
                        media = posts[0].get('graphql', {}).get('shortcode_media', {})
                        
                        # Handle single image/video
                        if media.get('display_url'):
                            media_url = media['display_url']
                            await download_media(media_url, f"{temp_dir}/media_1.jpg", headers)
                            downloaded_files.append(f"{temp_dir}/media_1.jpg")
                        
                        # Handle video
                        if media.get('video_url'):
                            video_url = media['video_url']
                            await download_media(video_url, f"{temp_dir}/video_1.mp4", headers)
                            downloaded_files.append(f"{temp_dir}/video_1.mp4")
                        
                        # Handle carousel (multiple images/videos)
                        carousel = media.get('edge_sidecar_to_children', {}).get('edges', [])
                        for i, item in enumerate(carousel):
                            node = item.get('node', {})
                            if node.get('display_url'):
                                await download_media(node['display_url'], f"{temp_dir}/carousel_{i+1}.jpg", headers)
                                downloaded_files.append(f"{temp_dir}/carousel_{i+1}.jpg")
                            if node.get('video_url'):
                                await download_media(node['video_url'], f"{temp_dir}/carousel_video_{i+1}.mp4", headers)
                                downloaded_files.append(f"{temp_dir}/carousel_video_{i+1}.mp4")
                                
                except Exception as e:
                    print(f"JSON parsing error: {e}")
            
            # Fallback: Extract media URLs using regex
            if not downloaded_files:
                # Look for image URLs
                img_patterns = [
                    r'"display_url":"([^"]+)"',
                    r'"src":"([^"]*instagram[^"]*\.jpg[^"]*)"',
                    r'content="([^"]*instagram[^"]*\.jpg[^"]*)"'
                ]
                
                for pattern in img_patterns:
                    img_matches = re.findall(pattern, content)
                    for i, img_url in enumerate(set(img_matches)):
                        if 'instagram' in img_url and 'jpg' in img_url:
                            img_url = img_url.replace('\\u0026', '&')
                            filename = f"{temp_dir}/fallback_img_{i+1}.jpg"
                            if await download_media(img_url, filename, headers):
                                downloaded_files.append(filename)
                
                # Look for video URLs
                video_patterns = [
                    r'"video_url":"([^"]+)"',
                    r'"src":"([^"]*instagram[^"]*\.mp4[^"]*)"'
                ]
                
                for pattern in video_patterns:
                    video_matches = re.findall(pattern, content)
                    for i, video_url in enumerate(set(video_matches)):
                        if 'instagram' in video_url and 'mp4' in video_url:
                            video_url = video_url.replace('\\u0026', '&')
                            filename = f"{temp_dir}/fallback_video_{i+1}.mp4"
                            if await download_media(video_url, filename, headers):
                                downloaded_files.append(filename)
            
            if downloaded_files:
                return True, f"Downloaded {len(downloaded_files)} files"
            else:
                return False, "No media content found in the post"
        else:
            return False, f"Could not access Instagram page (HTTP {response.status_code})"
            
    except Exception as e:
        return False, f"Download error: {str(e)}"

async def download_media(url, filename, headers):
    """Download a single media file"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Failed to download media: {e}")
    return False

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
        for image in images:
            try:
                await client.send_photo(chat_id, image, caption="📸 Downloaded from Instagram")
                uploaded += 1
                await asyncio.sleep(0.5)  # Small delay to avoid flooding
            except Exception as e:
                print(f"Failed to upload image: {e}")
                
        # Upload videos
        for video in videos:
            try:
                await client.send_video(chat_id, video, caption="🎥 Downloaded from Instagram")
                uploaded += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Failed to upload video: {e}")
            
        await status_msg.edit_text(f"✅ Successfully uploaded {uploaded} out of {total} files!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload error: {str(e)}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = """
🤖 **Working Instagram Downloader Bot**

Send me Instagram links and I'll download the content for you!

**What I can download:**
📸 Instagram Posts
🎥 Instagram Reels  
📺 IGTV Videos
🖼️ Carousel Posts (multiple images)

**Features:**
✅ Multiple download methods
✅ Better Instagram compatibility
✅ Handles both images and videos
✅ Works with public content

**Usage:**
Just send any Instagram URL:
• `https://instagram.com/p/ABC123/`
• `https://instagram.com/reel/XYZ789/`

Try it now! 🚀
"""
    await message.reply_text(text)

@app.on_message(filters.command("help"))
async def help_cmd(client, message):
    text = """
📋 **How to Use**

1. **Copy Instagram URL** 📋
   Copy the link from any Instagram post or reel

2. **Send to Bot** 📤
   Paste the URL and send it to me

3. **Wait for Download** ⏳
   I'll process and download the content

4. **Receive Files** ✅
   Get the images/videos sent to you

**Supported URLs:**
• Posts: `instagram.com/p/ABC123/`
• Reels: `instagram.com/reel/XYZ789/`
• IGTV: `instagram.com/tv/ABC123/`

**Important Notes:**
⚠️ Only public content can be downloaded
⚠️ Some content may be restricted by Instagram
⚠️ Large files may take time to process

**Need help?** Just send /start to see the main menu.
"""
    await message.reply_text(text)

@app.on_message(filters.regex(r'instagram\.com'))
async def handle_url(client, message):
    url = message.text.strip()
    status = await message.reply_text("🔄 Processing Instagram URL...")
    
    temp_dir = f"/tmp/ig_{message.from_user.id}_{uuid.uuid4().hex[:8]}"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        shortcode = extract_shortcode(url)
        if not shortcode:
            await status.edit_text("❌ Invalid Instagram URL format.\n\n✅ **Supported formats:**\n• instagram.com/p/ABC123/\n• instagram.com/reel/XYZ789/\n• instagram.com/tv/ABC123/")
            return
        
        await status.edit_text("📥 Extracting content from Instagram...")
        
        success, result_message = await download_instagram_content(url, temp_dir)
        
        if success:
            await status.edit_text("📤 Uploading downloaded content...")
            await upload_files(client, message.chat.id, temp_dir, status)
        else:
            await status.edit_text(f"""❌ **Download Failed**
            
{result_message}

**Possible reasons:**
• Content is private or restricted
• Instagram is blocking the request
• Post was deleted or doesn't exist
• Temporary server issues

**Try:**
• Make sure the post is public
• Wait a few minutes and try again
• Check if the URL is correct""")
        
    except Exception as e:
        await status.edit_text(f"❌ Unexpected error: {str(e)}\n\nPlease try again later.")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 Starting Working Instagram Bot...")
    print("✅ Bot is ready to download Instagram content!")
    app.run()