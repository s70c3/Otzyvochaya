import logging
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from aiogram.utils.executor import start_webhook
from config import WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from typing import List, Union
from db import database
from aiogram.dispatcher.filters.state import State, StatesGroup

import aiogram.utils.markdown as md

from registration_teacher import *
from registration_student import *

async def on_startup(dispatcher):
    await database.connect()
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await database.disconnect()
    await bot.delete_webhook()



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )