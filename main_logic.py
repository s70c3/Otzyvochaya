
import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor

from config import dp, bot
from db import database

# States
class Work_Form(StatesGroup):
    login_input = State()  # Will be represented in storage as 'Form:name'
    password_input = State()  # Will be represented in storage as 'Form:level'
    select_operation = State()
    select_compliment = State()
    input_negative = State()
    input_wish = State()
    select_subject = State()
    select_subject_mark = State()
    select_content_mark = State()
    select_student = State()
    select_mark = State()
    input_wish = State()


@dp.message_handler(commands='login')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Work_Form.login_input.set()

    await message.reply("Введите ваш логин.")

@dp.message_handler(state=Work_Form.login_input)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['login'] = message.text

    await Work_Form.next()
    await message.reply("Введите пароль")


@dp.message_handler(state=Work_Form.password_input)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text

    user = await database.fetch_one('SELECT * '
                                        'FROM teachers '
                                        'WHERE login = :login ',
                                        values={'login': data['login']})


    # await Work_Form.next()
    await message.answer(user.values())