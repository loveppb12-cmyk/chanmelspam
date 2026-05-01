import asyncio
import random
import os
import signal
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

TOKEN = "8688313238:AAEVUXCQICAMM_7x9gD0tOo5eaLHK83uFjA"
OWNER_ID = 8595518118

# Store active channels and their settings
active_channels = {}
MESSAGES = ["Hi", "india", "hindi", "crypto", "hi"]
INTERVALS = [5, 10, 15]

# Global application object
application = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
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
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
        
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                f"❌ Bot is not admin in channel {channel_id}\n"
                f"Please add bot as admin with all permissions first!"
            )
            return
        
        if channel_id in active_channels:
            active_channels[channel_id]["enabled"] = True
            await update.message.reply_text(f"✅ Resumed sending to channel `{channel_id}`", parse_mode="Markdown")
        else:
            active_channels[channel_id] = {"interval_index": 0, "enabled": True}
            await update.message.reply_text(
                f"✅ Started sending to channel `{channel_id}`\n"
                f"⏱️ Cycle: 5s → 10s → 15s → repeat",
                parse_mode="Markdown"
            )
            
    except TelegramError as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stop command"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized")
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
        await update.message.reply_text(f"🛑 Stopped sending to channel `{channel_id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Channel `{channel_id}` not active", parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if not active_channels:
        await update.message.reply_text("📊 No active channels.\nUse `/start channel_id` to add a channel.")
        return
    
    status_text = "📊 *Active Channels:*\n\n"
    for channel_id, data in active_channels.items():
        status = "✅ Active" if data["enabled"] else "⏸️ Stopped"
        status_text += f"• Channel: `{channel_id}`\n  Status: {status}\n\n"
    
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

async def message_sender_loop():
    """Background task to send messages"""
    global application, active_channels
    
    while True:
        try:
            for channel_id, data in list(active_channels.items()):
                if data["enabled"] and application and application.bot:
                    interval_index = data["interval_index"]
                    message = random.choice(MESSAGES)
                    await send_message_to_channel(application.bot, channel_id, message)
                    data["interval_index"] = (interval_index + 1) % len(INTERVALS)
                    wait_time = INTERVALS[interval_index]
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(5)
        except Exception as e:
            print(f"Error in message loop: {e}")
            await asyncio.sleep(10)

async def post_init(app: Application):
    """Start background task after bot is initialized"""
    global application
    application = app
    asyncio.create_task(message_sender_loop())
    print("✅ Bot is ready! Send /start [channel_id] to begin")

def handle_shutdown(signum, frame):
    """Handle shutdown gracefully"""
    print("Received shutdown signal, stopping bot...")
    if application:
        application.stop()
    sys.exit(0)

def main():
    """Start the bot"""
    global application
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    # Create application
    application = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    
    print("🤖 Bot starting on Heroku...")
    print("👤 Owner ID:", OWNER_ID)
    print("💬 Commands: /start, /stop, /status")
    
    # Start the bot with proper polling settings
    application.run_polling(allowed_updates=["message", "chat_member"])

if __name__ == "__main__":
    main()
