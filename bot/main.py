import asyncio
import logging
import time
import json
import requests
import matplotlib.pyplot as plt
from aiogram import Bot, Dispatcher, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

import bot_config

bot = Bot(token=bot_config.BOT_TOKEN, parse_mode=ParseMode.HTML)
router = Router()
usernames = set()
is_tracking = False

@router.message(Command("start"))
async def start_handler(msg: Message):
    usernames.add((msg.from_user.username, msg.from_user.first_name, msg.from_user.last_name, msg.from_user.id))
    print(usernames)
    await msg.answer("Welcome to BBT_manipulator bot\n\nCommands list:\n/track - start tracking\n/notrack - stop tracking\n/part_graph - plot part data graph (or cat)\n/full_graph - plot full data graph")

@router.message(Command("track"))
async def track_handler(msg: Message):
    global is_tracking 
    is_tracking = True   
    while is_tracking == True:
        try:
            response = requests.get("http://nginx_server_container:1010/get_cur_price/USDT-BTC").json()
            await msg.answer("BTC/USDT: " + str(response["USDT-BTC"]))
            time.sleep(bot_config.TRACKING_PAUSE_SEC)
        except Exception as e:
            print(e)
            await msg.answer("Sample is preparing")
            time.sleep(bot_config.TRACKING_PAUSE_SEC)

@router.message(Command("notrack"))
async def notrack_handler(msg: Message):
    global is_tracking
    is_tracking = False
    await msg.answer("Tracking stopped")

@router.message(Command("part_graph"))
async def part_graph_handler(msg: Message):
    try:
        response = requests.get("http://nginx_server_container:1010/get_part_graph_data").json()
        graph_data = json.loads(response)
        print(graph_data)
        plt.plot(range(bot_config.TIME_WINDOW_SIZE), graph_data[-bot_config.TIME_WINDOW_SIZE:])
        plt.xlabel("time samples")
        plt.ylabel("price")
        plt.savefig("graph.png")
        plt.close()
        graph = FSInputFile("graph.png")
        await bot.send_photo(photo=graph, chat_id=msg.from_user.id)
    except Exception as e:
        print(e)
        cat = FSInputFile("strange.jpg")
        await bot.send_photo(photo=cat, chat_id=msg.from_user.id, caption="Graph is not ready yet, have a cat")

@router.message(Command("full_graph"))
async def full_graph_handler(msg: Message):
    try:
        response = requests.get("http://nginx_server_container:1010/get_full_graph_data").json()
        full_graph_data = json.loads(response)
        print(full_graph_data)
        plt.plot(range(len(full_graph_data)), full_graph_data)
        plt.xlabel("time samples")
        plt.ylabel("price")
        plt.savefig("graph.png")
        plt.close()
        graph = FSInputFile("graph.png")
        await bot.send_photo(photo=graph, chat_id=msg.from_user.id)
    except Exception as e:
        print(e)
        cat = FSInputFile("strange.jpg")
        await bot.send_photo(photo=cat, chat_id=msg.from_user.id, caption="Graph is not ready yet, have a cat")

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()) 


logging.basicConfig(level=logging.INFO)
asyncio.run(main())