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

# NEW: Extract message ID from Telegram message link
async def extract_msg_id(link):
    match = re.search(r"/(-?\d+)/(\d+)", link)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

# NEW: Start range-based forwarding with logging, limit and flood control
MAX_MESSAGES = 500  # prevent overload, only for range command

async def range_forward(client, from_chat_id, to_chat_id, start_id, end_id, delay=Config.DELAY, batch=Config.BATCH):
    total = end_id - start_id + 1
    # Apply limit only for /range, not the default clone process
    if temp.FWD_SESS.get("__range_mode__") and total > MAX_MESSAGES:
        logger.warning(f"Range too big: {total} messages. Max allowed is {MAX_MESSAGES}.")
        return

    try:
        msg_ids = list(range(start_id, end_id + 1))
        logger.info(f"Starting forwarding from {start_id} to {end_id} (Total: {len(msg_ids)})")

        for i in range(0, len(msg_ids), batch):
            batch_ids = msg_ids[i:i+batch]
            logger.info(f"Forwarding batch: {batch_ids}")
            try:
                await client.forward_messages(to_chat_id, from_chat_id, batch_ids)
            except FloodWait as e:
                wait_time = max(e.value, 60)  # force minimum wait of 60 seconds
                logger.warning(f"FloodWait: sleeping for {wait_time} seconds")
                await asyncio.sleep(wait_time)
                await client.forward_messages(to_chat_id, from_chat_id, batch_ids)

            await asyncio.sleep(delay)

        logger.info("✅ Range forwarding completed.")

    except Exception as ex:
        logger.error(f"Error during range forward: {ex}")

# MODIFIED: Main callback for forwarding entry
@Client.on_message(filters.command("range"))
async def custom_range_forward(client, message):
    try:
        args = message.text.split()
        if len(args) != 3:
            return await message.reply("Usage: /range <start_msg_link> <end_msg_link>")

        start_link, end_link = args[1], args[2]
        from_chat_id, start_id = await extract_msg_id(start_link)
        _, end_id = await extract_msg_id(end_link)

        if not all([from_chat_id, start_id, end_id]):
            return await message.reply("Invalid message links")

        # Ask user for target chat
        temp.FWD_SESS[message.from_user.id] = {
            'from': from_chat_id,
            'start_id': start_id,
            'end_id': end_id,
            'step': 'await_target'
        }
        temp.FWD_SESS["__range_mode__"] = True
        await message.reply("Send me the target channel username or ID")

    except Exception as e:
        await message.reply(f"Error: {str(e)}")

# Handle follow-up message for target chat
@Client.on_message(filters.text & filters.private)
async def handle_target_chat(client, message):
    user_id = message.from_user.id
    session = temp.FWD_SESS.get(user_id)
    if session and session.get('step') == 'await_target':
        to_chat_id = message.text.strip()
        await range_forward(client, session['from'], to_chat_id, session['start_id'], session['end_id'])
        await message.reply("✅ Messages forwarded from range.")
        del temp.FWD_SESS[user_id]
        temp.FWD_SESS.pop("__range_mode__", None)
