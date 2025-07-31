"""
Utility functions for Instagram content downloading and uploading
"""

import os
import glob
import shutil
from pyrogram.types import InputMediaPhoto, InputMediaVideo
from pyrogram.errors import FloodWait
import asyncio

async def download_and_upload_content(client, chat_id, temp_dir, status_msg):
    """Download and upload Instagram content to Telegram"""
    
    try:
        # Find all downloaded files
        images = glob.glob(f"{temp_dir}/*.jpg") + glob.glob(f"{temp_dir}/*.jpeg")
        videos = glob.glob(f"{temp_dir}/*.mp4") + glob.glob(f"{temp_dir}/*.mov")
        
        total_files = len(images) + len(videos)
        
        if total_files == 0:
            await status_msg.edit_text("❌ No content found to upload.")
            return
            
        await status_msg.edit_text(f"📤 Found {total_files} files. Uploading...")
        
        uploaded = 0
        
        # Upload images
        if len(images) == 1:
            # Single image
            await client.send_photo(chat_id, images[0])
            uploaded += 1
            
        elif len(images) > 1:
            # Multiple images as album (max 10 per album)
            for i in range(0, len(images), 10):
                chunk = images[i:i + 10]
                media_group = [InputMediaPhoto(img) for img in chunk]
                
                try:
                    await client.send_media_group(chat_id, media_group)
                    uploaded += len(chunk)
                    
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await client.send_media_group(chat_id, media_group)
                    uploaded += len(chunk)
                    
                # Update status
                await status_msg.edit_text(f"📤 Uploaded {uploaded}/{total_files} files...")
        
        # Upload videos
        for video in videos:
            try:
                await client.send_video(chat_id, video)
                uploaded += 1
                await status_msg.edit_text(f"📤 Uploaded {uploaded}/{total_files} files...")
                
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await client.send_video(chat_id, video)
                uploaded += 1
                await status_msg.edit_text(f"📤 Uploaded {uploaded}/{total_files} files...")
        
        # Success message
        await status_msg.edit_text(f"✅ Successfully uploaded {uploaded} files!")
        
        # Add source info
        await client.send_message(
            chat_id,
            "📥 **Downloaded via Instagram Bot**\n\n"
            "💡 Send me more Instagram links to download!\n"
            "🔐 Use /login for private content access"
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Upload failed: {str(e)}")
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def extract_content_info(post_or_reel):
    """Extract information from Instagram post/reel"""
    try:
        info = {
            'username': post_or_reel.owner_username,
            'caption': post_or_reel.caption[:500] if post_or_reel.caption else "No caption",
            'likes': post_or_reel.likes,
            'comments': post_or_reel.comments,
            'date': post_or_reel.date_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            'is_video': post_or_reel.is_video
        }
        return info
    except:
        return None

async def send_content_info(client, chat_id, info):
    """Send content information to user"""
    if not info:
        return
        
    info_text = f"""
📊 **Content Info:**

👤 **User:** @{info['username']}
❤️ **Likes:** {info['likes']:,}
💬 **Comments:** {info['comments']:,}
📅 **Date:** {info['date']}
🎥 **Type:** {'Video' if info['is_video'] else 'Photo'}

📝 **Caption:**
{info['caption']}
"""
    
    await client.send_message(chat_id, info_text)