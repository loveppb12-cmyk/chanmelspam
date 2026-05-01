import asyncio
import random
import os
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

TOKEN = os.environ.get("8688313238:AAF8-e_9RlUAq9cZy70xkITUCCG6WyqCsTQ", "YOUR_TOKEN_HERE")
OWNER_ID = 8595518118  # Your owner ID

# Store active channels and their settings
active_channels = {}  # {channel_id: {"interval_index": 0, "enabled": True}}
MESSAGES = ["Hi", "india", "hindi", "crypto", "hi"]
INTERVALS = [5, 10, 15]

# Global variables
bot_instance = None
message_loop_task = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    # Check if channel ID provided
    if len(context.args) == 0:
        await update.message.reply_text(
            "📌 *Usage:*\n"
            "`/start channel_id` - Start sending messages to channel\n"
            "`/stop channel_id` - Stop sending messages to channel\n"
            "`/status` - Show all active channels\n\n"
            "Example: `/start -1001234567890`\n\n"
            "How to get channel ID:\n"
            "1. Add @username_to_id_bot to your channel\n"
            "2. Send any message and it will show channel ID",
            parse_mode="Markdown"
        )
        return
    
    try:
        channel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid channel ID. Must be a number.")
        return
    
    # Try to verify bot is admin
    try:
        chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
        
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                f"❌ Bot is not admin in channel {channel_id}\n"
                f"Please add bot as admin with all permissions first!"
            )
            return
        
        # Start sending messages
        if channel_id in active_channels:
            active_channels[channel_id]["enabled"] = True
            await update.message.reply_text(f"✅ Resumed sending messages to channel `{channel_id}`", parse_mode="Markdown")
        else:
            active_channels[channel_id] = {"interval_index": 0, "enabled": True}
            await update.message.reply_text(
                f"✅ Started sending messages to channel `{channel_id}`\n"
                f"📝 Bot is admin: Yes\n"
                f"⏱️ Message cycle: 5s → 10s → 15s → repeat",
                parse_mode="Markdown"
            )
            
    except TelegramError as e:
        await update.message.reply_text(f"❌ Error: {e}\nMake sure channel ID is correct and bot is added as admin")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    if len(context.args) == 0:
        await update.message.reply_text("Usage: `/stop channel_id`", parse_mode="Markdown")
        return
    
    try:
        channel_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid channel ID.")
        return
    
    if channel_id in active_channels:
        active_channels[channel_id]["enabled"] = False
        await update.message.reply_text(f"🛑 Stopped sending messages to channel `{channel_id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Channel `{channel_id}` is not active", parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    if not active_channels:
        await update.message.reply_text("📊 No active channels.\nUse `/start channel_id` to add a channel.")
        return
    
    status_text = "📊 *Active Channels:*\n\n"
    for channel_id, data in active_channels.items():
        status = "✅ Active" if data["enabled"] else "⏸️ Stopped"
        status_text += f"• Channel: `{channel_id}`\n  Status: {status}\n  Cycle position: {data['interval_index']}\n\n"
    
    await update.message.reply_text(status_text, parse_mode="Markdown")

async def send_message_to_channel(bot, channel_id, message):
    """Send message to a specific channel"""
    try:
        await bot.send_message(chat_id=channel_id, text=message)
        print(f"✓ Sent '{message}' to {channel_id}")
        return True
    except TelegramError as e:
        print(f"✗ Failed to send to {channel_id}: {e}")
        return False

async def message_sender_loop(application: Application):
    """Background task to send messages to all active channels"""
    global active_channels
    
    while True:
        try:
            for channel_id, data in list(active_channels.items()):
                if data["enabled"]:
                    # Get current interval index
                    interval_index = data["interval_index"]
                    
                    # Send random message
                    message = random.choice(MESSAGES)
                    await send_message_to_channel(application.bot, channel_id, message)
                    
                    # Update interval index for next time
                    data["interval_index"] = (interval_index + 1) % len(INTERVALS)
                    
                    # Wait based on current interval
                    wait_time = INTERVALS[interval_index]
                    await asyncio.sleep(wait_time)
                else:
                    # Channel disabled, check every 10 seconds
                    await asyncio.sleep(10)
                    
        except Exception as e:
            print(f"Error in message loop: {e}")
            await asyncio.sleep(5)

async def post_init(application: Application):
    """Start background task after bot is initialized"""
    asyncio.create_task(message_sender_loop(application))

def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    
    print("🤖 Bot started! Owner ID:", OWNER_ID)
    print("📝 Commands:")
    print("  /start channel_id - Start sending to channel")
    print("  /stop channel_id - Stop sending to channel")
    print("  /status - Show all active channels")
    
    # Start the bot
    application.run_polling(allowed_updates=["chat_member", "my_chat_member"])

if __name__ == "__main__":
    main()
