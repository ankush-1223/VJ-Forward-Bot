from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from script import Script

@Client.on_message(filters.command("start") & filters.private)
async def start_message(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📤 Forward Range", callback_data="range_mode")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")],
        ]
    )
    await message.reply_text(
        text=f"👋 Hello {message.from_user.mention}!\n\nWelcome to the Telegram Cloner Bot.\nUse the menu below to start.",
        reply_markup=keyboard
    )
