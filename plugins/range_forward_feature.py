
# Don't Remove Credit Tg - @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot https://youtube.com/@Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import sys 
import math
import time, re
import asyncio 
import logging
import random
from .utils import STS
from database import Db, db
from .test import CLIENT, get_client, iter_messages
from config import Config, temp
from script import Script
from pyrogram import Client, filters 
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 
from .db import connect_user_db
from pyrogram.types import Message

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Script.TEXT

# Extract message ID from Telegram message link
async def extract_msg_id(link):
    match = re.search(r"/(-?\d+)/(\d+)", link)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

# Range forwarding logic
MAX_MESSAGES = 500

async def range_forward(client, from_chat_id, to_chat_id, start_id, end_id, delay=Config.DELAY, batch=Config.BATCH):
    total = end_id - start_id + 1
    if temp.FWD_SESS.get("__range_mode__") and total > MAX_MESSAGES:
        await client.send_message(to_chat_id, f"❌ You can only forward up to {MAX_MESSAGES} messages in range mode.")
        return

    try:
        msg_ids = list(range(start_id, end_id + 1))
        await client.send_message(to_chat_id, f"🔁 Starting to forward {total} messages...")

        for i in range(0, len(msg_ids), batch):
            batch_ids = msg_ids[i:i+batch]
            try:
                await client.forward_messages(to_chat_id, from_chat_id, batch_ids)
            except FloodWait as e:
                wait_time = max(e.value, 60)
                await client.send_message(to_chat_id, f"⏱️ Rate limit hit. Sleeping for {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                await client.forward_messages(to_chat_id, from_chat_id, batch_ids)
            await asyncio.sleep(delay)

        await client.send_message(to_chat_id, "✅ Range forwarding completed.")

    except Exception as ex:
        await client.send_message(to_chat_id, f"❌ Error: {ex}")

# Range command handler
@Client.on_message(filters.command("range"))
async def custom_range_forward(client, message):
    try:
        await message.reply_text(
            "📝 Send me the first message link to begin range forwarding.",
        )
        temp.FWD_SESS[message.from_user.id] = {"step": "get_start"}
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# Handle step-based input for range
@Client.on_message(filters.text & filters.private)
async def handle_range_input(client, message):
    user_id = message.from_user.id
    session = temp.FWD_SESS.get(user_id)
    if not session:
        return

    step = session.get("step")
    text = message.text.strip()

    if step == "get_start":
        from_chat_id, start_id = await extract_msg_id(text)
        if not from_chat_id:
            return await message.reply("❌ Invalid message link. Send a valid start message link.")
        temp.FWD_SESS[user_id] = {
            "step": "get_end",
            "from": from_chat_id,
            "start_id": start_id
        }
        return await message.reply("✅ Now send the last message link of the range.")

    if step == "get_end":
        _, end_id = await extract_msg_id(text)
        if not end_id:
            return await message.reply("❌ Invalid message link. Send a valid end message link.")
        temp.FWD_SESS[user_id]["end_id"] = end_id
        temp.FWD_SESS[user_id]["step"] = "get_target"
        return await message.reply("📥 Now send the target chat ID or @username to forward messages to.")

    if step == "get_target":
        to_chat_id = text
        sess = temp.FWD_SESS[user_id]
        await range_forward(
            client,
            from_chat_id=sess["from"],
            to_chat_id=to_chat_id,
            start_id=sess["start_id"],
            end_id=sess["end_id"]
        )
        del temp.FWD_SESS[user_id]
        temp.FWD_SESS.pop("__range_mode__", None)
