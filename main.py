import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from io import BytesIO
import requests
import asyncio
from flask import Flask
from threading import Thread
import os

# Initialize Flask app
app = Flask(__name__)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Change to DEBUG to capture more detailed logs
)
logger = logging.getLogger(__name__)

# Telegram Bot Token and Owner ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "7106709057:AAEDzg7JSl0lTC-Nc5kcyKen6gYWLiywMdM")  # Make sure to set in Koyeb as env variable
OWNER_ID = int(os.getenv("OWNER_ID", "7137002799"))

# Channel details
channels = {
    "Channel 3": "-1002408234754"
}

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("Received /start command")

    # Image URL (can be hosted image URL or local file path)
    image_url = "https://i.ibb.co/Dk35rBs/66ef6566.jpg"  # Replace with your image URL
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
    except Exception as e:
        logger.error(f"Error sending image: {e}")

# Handle button press and send temporary invite link
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("Button clicked")
    query = update.callback_query
    await query.answer()

    # Generate a temporary link (expire in 10 seconds)
    try:
        expire_time = datetime.now() + timedelta(seconds=10)
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=query.data, expire_date=expire_time, member_limit=None
        )

        await query.message.reply_text(
            f"𝐇𝐞𝐲 𝐛𝐮𝐝𝐝𝐲 ✨✨\n\n𝐉𝐨𝐢𝐧 𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐂𝐡𝐚𝐧𝐧𝐞𝐥 𝐛𝐲 𝐭𝐡𝐢𝐬 𝐥𝐢𝐧𝐤: {invite_link.invite_link}\n\nNOTE:- This Link Automatic Revokes in 10sec so Join fast 🙏🙏"
        )

        # Schedule revocation after 10 seconds
        asyncio.create_task(revoke_invite_link(context.bot, query.data, invite_link.invite_link))

    except Exception as e:
        logger.error(f"Failed to generate link: {e}")
        await query.message.reply_text(f"Failed to generate link: {e}")

async def revoke_invite_link(bot, chat_id, invite_link):
    """Revoke the invite link after 10 seconds."""
    await asyncio.sleep(10)
    try:
        await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=invite_link)
        logger.info(f"Invite link {invite_link} has been revoked.")
    except Exception as e:
        logger.error(f"Failed to revoke link: {e}")

# /broadcast command handler (Owner-only)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id != OWNER_ID:
        await update.message.reply_text("You're not authorized to use this command.")
        return

    if context.args:
        message = " ".join(context.args)
        # Broadcast message to all users (in practice, maintain a user list in your database)
        await update.message.reply_text("Broadcasting message...")

        # In real implementation, you'd loop through user IDs and send the message to each
        try:
            for chat_id in [OWNER_ID]:  # Replace with a list of your bot users
                await context.bot.send_message(chat_id=chat_id, text=message)
            await update.message.reply_text("Message broadcasted successfully!")
        except Exception as e:
            await update.message.reply_text(f"Broadcast failed: {e}")
    else:
        await update.message.reply_text("Usage: /broadcast <message>")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Update {update} caused error {context.error}")

# Flask health check route
@app.route('/')
def index():
    return "Bot is running!"

# Function to run Telegram bot
async def run_telegram_bot():
    logger.info("Starting the Telegram bot...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("broadcast", broadcast))

    # Error handler
    application.add_error_handler(error_handler)

    # Start polling
    await application.start()
    logger.info("Bot is polling for updates...")
    await application.updater.start_polling()

if __name__ == '__main__':
    logger.info("Starting Flask server and Telegram bot")
    
    # Start Telegram bot in a separate thread
    loop = asyncio.get_event_loop()
    loop.create_task(run_telegram_bot())
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8080)
