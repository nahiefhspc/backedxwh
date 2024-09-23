import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError
from io import BytesIO
import requests
import asyncio
from datetime import datetime, timedelta

# Telegram Bot Token
BOT_TOKEN = '7106709057:AAEDzg7JSl0lTC-Nc5kcyKen6gYWLiywMdM'
OWNER_ID = 7137002799  # Replace with your owner ID

# Channel details (Make sure the bot is an admin in these channels)
channels = {
    "Channel 2": "-1002408234754"
}

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = "https://i.ibb.co/Dk35rBs/66ef6566.jpg"  # Replace with your image URL
    caption = "Welcome! Please choose a channel below to get a temporary invite link (valid for 10 seconds)."

    keyboard = [
        [InlineKeyboardButton(name, callback_data=channel)] for name, channel in channels.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        response = requests.get(image_url)
        image = BytesIO(response.content)

        await update.message.reply_photo(
            photo=InputFile(image),
            caption=caption,
            reply_markup=reply_markup
        )
    except TelegramError as e:
        logger.error(f"Error sending image: {e}")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        expire_time = datetime.now() + timedelta(seconds=10)
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=query.data, expire_date=expire_time, member_limit=None
        )

        await query.message.reply_text(f"Here is your invite link: {invite_link.invite_link}\n\nNote: This link will expire in 10 seconds!")
        asyncio.create_task(revoke_invite_link(context.bot, query.data, invite_link.invite_link))

    except TelegramError as e:
        await query.message.reply_text(f"Failed to generate link: {e}")

async def revoke_invite_link(bot, chat_id, invite_link):
    await asyncio.sleep(10)
    try:
        await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=invite_link)
        logger.info(f"Invite link {invite_link} has been revoked.")
    except TelegramError as e:
        logger.error(f"Failed to revoke link: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("You're not authorized to use this command.")
        return

    if context.args:
        message = " ".join(context.args)
        await update.message.reply_text("Broadcasting message...")
        try:
            for chat_id in [OWNER_ID]:  # Replace with your user list
                await context.bot.send_message(chat_id=chat_id, text=message)
            await update.message.reply_text("Message broadcasted successfully!")
        except TelegramError as e:
            await update.message.reply_text(f"Broadcast failed: {e}")
    else:
        await update.message.reply_text("Usage: /broadcast <message>")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Update {update} caused error {context.error}")

# Function to run the bot
def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == '__main__':
    run_bot()
