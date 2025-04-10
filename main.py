from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from script import Script

@Client.on_message(filters.command("start") & filters.private)
async def start_message(client, message):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📤 Forward Range", callback_data="range_mode")
            ],
            [
                InlineKeyboardButton("ℹ️ About", callback_data="about")
            ]
        ]
    )
    await message.reply_text(
        text=f"👋 Hello {message.from_user.mention}!

Welcome to the Telegram Cloner Bot.",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex("about"))
async def about_handler(client, callback_query):
    await callback_query.message.edit_text(
        "🤖 *Bot Info:*
This bot helps you clone messages between Telegram chats.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔙 Back", callback_data="start")]]
        )
    )

@Client.on_callback_query(filters.regex("start"))
async def back_to_home(client, callback_query):
    await start_message(client, callback_query.message)
