import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import asyncio
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
import json
import os
from aiohttp import ClientSession  # For faster HTTP requests

# Telegram Bot Token
BOT_TOKEN = '6811502626:AAG9xT3ZQUmg6CrdIPvQ0kCRJ3W5QL-fuZs'

# File to store channels
CHANNELS_FILE = 'channels.json'

# Load channels from file or use defaults
def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'r') as f:
            return json.load(f)
    return {
        "𝗖𝗹𝗮𝘀𝘀 𝟭𝟭𝘁𝗵|𝗟𝗶𝘃𝗲 🔴": "-1002469887330",
    }

# Save channels to file
def save_channels(channels_dict):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(channels_dict, f)

channels = load_channels()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask app for webhook
app = Flask(__name__)

# Global aiohttp session for faster requests
session = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    image_url = "https://i.ibb.co/D98tcdk/66f16ac7.jpg"
    caption = "<b>:..｡o○𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗯𝘂𝗱𝗱𝘆 🥰○o｡..:</b>\n\n" \
              "𝐓𝐡𝐚𝐧𝐤𝐬 𝐟𝐨𝐫 𝐜𝐨𝐦𝐢𝐧𝐠 𝐡𝐞𝐫𝐞 🙏🙏\n\n" \
              "𝐍𝐨𝐰 𝐂𝐥𝐢𝐜𝐤 𝐨𝐧 𝐛𝐞𝐥𝐨𝐰 𝐛𝐮𝐭𝐭𝐨𝐧𝐬 𝐭𝐨 𝐣𝐨𝐢𝐧 𝐨𝐧 𝐜𝐡𝐚𝐧𝐧𝐞𝐥 𝐰𝐡𝐚𝐭 𝐲𝐨𝐮 𝐰𝐚𝐧𝐭 ✨✨\n\n" \
              "<i>𝐈𝐟 𝐜𝐨𝐩𝐲𝐫𝐢𝐠𝐡𝐭 𝐨𝐧 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭 𝐬𝐚𝐯𝐞 𝐰𝐞𝐛𝐬𝐢𝐭𝐞 𝐟𝐨𝐫 𝐧𝐞𝐰 𝐛𝐨𝐭</i>\n" \
              "❀ <a href='https://yashyasag.github.io/botupdates'>Bot Updates</a>"

    keyboard = [[InlineKeyboardButton(name, callback_data=channel)] for name, channel in channels.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Faster image fetching with aiohttp
    async with session.get(image_url) as response:
        image_data = await response.read()

    await update.message.reply_photo(
        photo=image_data,
        caption=caption,
        parse_mode='HTML',
        reply_markup=reply_markup,
        protect_content=True  # Content protection enabled
    )

async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Please use the format:\n/add\nChannel name : channel_id\nChannel name2 : channel_id2",
            parse_mode='HTML'
        )
        return

    text = ' '.join(context.args).split('\n')
    added, errors = [], []
    
    for line in text:
        line = line.strip()
        if not line:
            continue
        try:
            if ':' not in line:
                errors.append(f"Invalid format: {line}")
                continue
            name, channel_id = [part.strip() for part in line.split(':', 1)]
            if not name or not channel_id or not channel_id.startswith('-100'):
                errors.append(f"Invalid data: {line}")
                continue
            channels[name] = channel_id
            added.append(name)
        except Exception as e:
            errors.append(f"Error: {line} - {str(e)}")

    save_channels(channels)
    response = ""
    if added:
        response += "<b>Added channels:</b>\n" + "\n".join(added) + "\n"
    if errors:
        response += "<b>Errors:</b>\n" + "\n".join(errors)
    
    await update.message.reply_text(response or "No valid channels added.", parse_mode='HTML')

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        expire_time = datetime.now() + timedelta(seconds=20)
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=query.data, 
            expire_date=expire_time, 
            member_limit=None
        )

        message = await query.message.reply_text(
            f"<b>𝐇𝐞𝐲,</b>\n"
            f"𝕃𝕚𝕟𝕜 𝕥𝕠 𝕛𝕠𝕚𝕟 𝕠𝕗 𝕪𝕠𝕦𝕣 𝕣𝕖𝕢𝕦𝕖𝕤𝕥 𝕔𝕙𝕒𝕟𝕟𝕖𝕝 👇👇\n\n"
            f"<a href='{invite_link.invite_link}'>𝗖𝗟𝗜𝗖𝗞 𝗧𝗢 𝗝𝗢𝗜𝗡 😈</a>\n\n"
            f"<i>𝐍𝐎𝐓𝐄 »» This link auto revoked in 20 seconds\n"
            f"So join fast or request again.</i>",
            parse_mode='HTML',
            protect_content=True,
            disable_web_page_preview=True
        )
        
        # Schedule message deletion and link revocation
        asyncio.create_task(handle_link_cleanup(context.bot, query.data, invite_link.invite_link, message))

    except Exception as e:
        await query.message.reply_text(f"Failed to generate link: {e}", parse_mode='HTML')

async def handle_link_cleanup(bot, chat_id, invite_link, message):
    await asyncio.sleep(30)  # Wait 30 seconds
    try:
        await bot.delete_message(chat_id=message.chat_id, message_id=message.message_id)
        await bot.revoke_chat_invite_link(chat_id=chat_id, invite_link=invite_link)
        logger.info(f"Invite link {invite_link} revoked and message deleted.")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"Update {update} caused error {context.error}")

def run_flask():
    app.run(host="0.0.0.0", port=8080)

async def run_telegram_bot():
    global session
    async with ClientSession() as session:  # Initialize aiohttp session
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("add", add_channel))
        application.add_handler(CallbackQueryHandler(button))
        application.add_error_handler(error_handler)
        await application.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(run_telegram_bot())
