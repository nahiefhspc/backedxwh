import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError
from io import BytesIO
import requests
import asyncio
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# Telegram Bot Token and Owner ID
BOT_TOKEN = '7106709057:AAEDzg7JSl0lTC-Nc5kcyKen6gYWLiywMdM'
OWNER_ID = 7137002799  # Replace with the owner ID

# Channel details (Make sure bot is an admin in these channels)
channels = {
    "Channel 1": "-1002408234754"
}

# Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = "https://i.ibb.co/Dk35rBs/66ef6566.jpg"
    caption = "Welcome! Please choose a channel below to get a temporary invite link (valid for 10 seconds)."
    
    # Prepare buttons with channels
    keyboard = [
        [InlineKeyboardButton(name, callback_data=channel)] for name, channel in channels.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Fetch and send the image
    try:
        response = requests.get(image_url)
        image = BytesIO(response.content)  # Prepare image in-memory

        await update.message.reply_photo(
            photo=InputFile(image),
            caption=caption,
            reply_markup=reply_markup
        )
    except TelegramError as e:
        logger.error(f"Error sending image: {e}")

# Handle button press and send temporary invite link
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Generate a temporary link (expire in 10 seconds)
    try:
        expire_time = datetime.now() + timedelta(seconds=10)
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=query.data, expire_date=expire_time
        )

        await query.message.reply_text(
            f"Join Requested Channel by this link: {invite_link.invite_link}\n\n"
            "NOTE: This Link will revoke automatically in 10 seconds."
        )

        # Schedule revocation after 10 seconds
        asyncio.create_task(revoke_invite_link(context.bot, query.data, invite_link.invite_link))

    except TelegramError as e:
        await query.message.reply_text(f"Failed to generate link: {e}")

async def revoke_invite_link(bot, chat_id, invite_link):
    """Revoke the invite link after 10 seconds."""
    await asyncio.sleep(10)  # Wait for 10 seconds
    try:
        await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=invite_link)
        logger.info(f"Invite link {invite_link} has been revoked.")
    except TelegramError as e:
        logger.error(f"Failed to revoke link: {e}")

# /broadcast command handler (Owner-only)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("You're not authorized to use this command.")
        return

    if context.args:
        message = " ".join(context.args)
        await update.message.reply_text("Broadcasting message...")

        try:
            for chat_id in [OWNER_ID]:  # Replace with a list of your bot users
                await context.bot.send_message(chat_id=chat_id, text=message)
            await update.message.reply_text("Message broadcasted successfully!")
        except TelegramError as e:
            await update.message.reply_text(f"Broadcast failed: {e}")
    else:
        await update.message.reply_text("Usage: /broadcast <message>")

# Flask route for health check
@app.route('/')
def index():
    return "Bot is running!"

# Run the Telegram bot
def run_telegram_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.run_polling()

if __name__ == '__main__':
    # Start the Telegram bot in a separate thread
    Thread(target=run_telegram_bot).start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8080)
