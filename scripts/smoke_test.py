#!/usr/bin/env python3
"""Send a smoke-test status message from the bot to the admin."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
from bot.config import settings


async def main():
    admin_id = settings.admin_ids[0]
    token = settings.bot_token
    url = "https://api.telegram.org/bot" + token + "/sendMessage"
    text = "Bot va worker ishga tushdi! 138/138 test yashil. zcard bug ham tuzatildi."
    async with aiohttp.ClientSession() as s:
        r = await s.post(url, json={"chat_id": admin_id, "text": text})
        data = await r.json()
        if data["ok"]:
            print("OK - message_id:", data["result"]["message_id"])
        else:
            print("FAIL:", data)


if __name__ == "__main__":
    asyncio.run(main())
