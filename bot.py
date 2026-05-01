import asyncio
import random
import os
import signal
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.error import TelegramError
import time

TOKEN = "8688313238:AAEVUXCQICAMM_7x9gD0tOo5eaLHK83uFjA"
OWNER_ID = 8595518118

# Store active channels
active_channels = {}
MESSAGES = ["Hi", "india", "hindi", "crypto", "hi"]
INTERVALS = [5, 10, 15]

# Global variables
bot_app = None
message_task = None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    try:
        user_id = update.effective_user.id
        
        if user_id != OWNER_ID:
            await update.message.reply_text("❌ You are not authorized to use this bot.")
            return
        
        if len(context.args) == 0:
            await update.message.reply_text(
                "📌 *How to use:*\n\n"
                "1. Add bot as admin to your channel\n"
                "2. Get channel ID from @userinfobot\n"
                "3. Send: `/start -1001234567890`\n\n"
                "📝 *Commands:*\n"
                "`/start channel_id` - Start bot in channel\n"
                "`/stop channel_id` - Stop bot in channel\n"
                "`/status` - Show active channels\n"
                "`/help` - Show this message",
                parse_mode="Markdown"
            )
            return
        
        try:
            channel_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid channel ID. Must be a number like: -1001234567890")
            return
        
        # Check if bot is admin
        try:
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
            
            if chat_member.status not in ['administrator', 'creator']:
                await update.message.reply_text(
                    f"❌ Bot is not admin in this channel!\n"
                    f"Please add @{context.bot.username} as admin first."
                )
                return
            
            # Add to active channels
            if channel_id not in active_channels:
                active_channels[channel_id] = {
                    "enabled": True,
                    "last_index": 0,
                    "last_time": time.time()
                }
                await update.message.reply_text(
                    f"✅ Bot started in channel!\n"
                    f"📢 Channel ID: `{channel_id}`\n"
                    f"⏱️ Sending every: 5s → 10s → 15s (repeat)\n"
                    f"💬 Messages: {', '.join(MESSAGES)}",
                    parse_mode="Markdown"
                )
            else:
                active_channels[channel_id]["enabled"] = True
                await update.message.reply_text(f"✅ Bot resumed in channel `{channel_id}`", parse_mode="Markdown")
                
        except TelegramError as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}\nMake sure channel ID is correct and bot is admin.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

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
        await update.message.reply_text("❌ Invalid channel ID")
        return
    
    if channel_id in active_channels:
        active_channels[channel_id]["enabled"] = False
        await update.message.reply_text(f"🛑 Stopped sending to channel `{channel_id}`", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ Channel `{channel_id}` is not active", parse_mode="Markdown")

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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "🤖 *Bot Commands:*\n\n"
        "`/start channel_id` - Start bot in a channel\n"
        "`/stop channel_id` - Stop bot in a channel\n"
        "`/status` - Show all active channels\n"
        "`/help` - Show this message\n\n"
        "*How to get channel ID:*\n"
        "1. Add @userinfobot to your channel\n"
        "2. Forward any message from channel to @userinfobot\n"
        "3. It will show the channel ID\n\n"
        "*Note:* Bot must be admin in the channel!",
        parse_mode="Markdown"
    )

async def send_messages():
    """Background task to send messages"""
    global bot_app, active_channels
    
    while True:
        try:
            if bot_app and bot_app.bot:
                for channel_id, data in list(active_channels.items()):
                    if data.get("enabled", False):
                        # Send random message
                        message = random.choice(MESSAGES)
                        try:
                            await bot_app.bot.send_message(chat_id=channel_id, text=message)
                            print(f"✓ Sent '{message}' to {channel_id}")
                        except Exception as e:
                            print(f"✗ Failed to send to {channel_id}: {e}")
                            if "chat not found" in str(e).lower():
                                active_channels.pop(channel_id, None)
                        
                        # Wait based on cycle (but don't block other channels)
                        await asyncio.sleep(5)  # Small delay between channels
                        
        except Exception as e:
            print(f"Error in send_messages: {e}")
        
        # Wait before next cycle
        await asyncio.sleep(3)

async def post_init(app: Application):
    """Initialize after bot starts"""
    global bot_app
    bot_app = app
    print("✅ Bot is ready!")
    print(f"👤 Owner ID: {OWNER_ID}")
    print("💬 Bot is listening for commands...")
    
    # Start background task
    asyncio.create_task(send_messages())

def handle_shutdown(signum, frame):
    """Handle shutdown gracefully"""
    print("Received shutdown signal, stopping bot...")
    if bot_app:
        bot_app.stop()
    sys.exit(0)

def main():
    """Start the bot"""
    global bot_app
    
    # Setup signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    # Create application
    bot_app = Application.builder().token(TOKEN).post_init(post_init).build()
    
    # Add command handlers
    bot_app.add_handler(CommandHandler("start", start_command))
    bot_app.add_handler(CommandHandler("stop", stop_command))
    bot_app.add_handler(CommandHandler("status", status_command))
    bot_app.add_handler(CommandHandler("help", help_command))
    
    print("🤖 Bot starting on Heroku...")
    print(f"📝 Bot token: {TOKEN[:10]}...")
    
    # Start polling (this will block)
    bot_app.run_polling(allowed_updates=["message"])

if __name__ == "__main__":
    main()
