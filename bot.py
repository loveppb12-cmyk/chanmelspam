import asyncio
import random
import os
from telegram import Bot
from telegram.error import TelegramError

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_TOKEN_HERE")  # Use environment variable

MESSAGES = ["Hi", "india", "hindi", "crypto", "hi"]
INTERVALS = [5, 10, 15]  # Seconds cycle

async def send_message(bot, channel_id, message):
    try:
        await bot.send_message(chat_id=channel_id, text=message)
        print(f"✓ Sent '{message}' to {channel_id}")
        return True
    except TelegramError as e:
        print(f"✗ Failed to send to {channel_id}: {e}")
        return False

async def get_admin_channels(bot):
    """Get all channels where bot is admin"""
    admin_channels = []
    
    try:
        # Get bot's updates to find channels
        updates = await bot.get_updates(allowed_updates=['chat_member', 'my_chat_member'])
        
        for update in updates:
            if update.my_chat_member:
                chat = update.my_chat_member.chat
                status = update.my_chat_member.new_chat_member.status
                
                if chat.type in ['channel', 'supergroup'] and status in ['administrator', 'creator']:
                    if chat.id not in admin_channels:
                        admin_channels.append(chat.id)
                        print(f"✓ Found channel: {chat.title or chat.id}")
            
            if update.chat_member:
                chat = update.chat_member.chat
                status = update.chat_member.new_chat_member.status
                
                if chat.type in ['channel', 'supergroup'] and status in ['administrator', 'creator']:
                    if chat.id not in admin_channels:
                        admin_channels.append(chat.id)
                        print(f"✓ Found channel: {chat.title or chat.id}")
                        
    except TelegramError as e:
        print(f"Error getting updates: {e}")
    
    return admin_channels

async def main():
    bot = Bot(token=TOKEN)
    interval_index = 0
    known_channels = set()
    
    print("🤖 Bot started on Heroku")
    print("📌 Add bot as admin to any channel and it will auto-detect!\n")
    
    while True:
        try:
            # Get fresh list of channels
            current_channels = await get_admin_channels(bot)
            
            if current_channels:
                known_channels.update(current_channels)
                
                # Send to all known channels
                for channel_id in known_channels:
                    message = random.choice(MESSAGES)
                    await send_message(bot, channel_id, message)
                
                # Cycle intervals
                wait_time = INTERVALS[interval_index % len(INTERVALS)]
                interval_index = (interval_index + 1) % len(INTERVALS)
                await asyncio.sleep(wait_time)
            else:
                print("⏳ No channels yet. Add bot to a channel with admin rights...")
                await asyncio.sleep(30)
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
