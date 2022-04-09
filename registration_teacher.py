
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

import logging


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    subject = State()  # Will be represented in storage as 'Form:subject'
    login = State()
    password = State()


@dp.message_handler(commands='register_teacher')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.name.set()

    await message.reply("Как вас зовут? Введите полное ФИО.")


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Русский язык", "Математика",  "Иностранный язык", "Физика",
               "Информатика", "Технология", "География", "Биология", "Химия")
    markup.add("Другой")

    await message.reply("Какой предмет вы преподаете?", reply_markup=markup)



# # Check age. Age gotta be digit
# @dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
# async def process_age_invalid(message: types.Message):
#     """
#     If age is invalid
#     """
#     return await message.reply("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message_handler(lambda message: message.text not in ["Русский язык", "Математика",  "Иностранный язык", "Физика",
               "Информатика", "Технология", "География", "Биология", "Химия", "Другой"], state=Form.subject)
async def process_gender_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Неизвестный предмет. Введите другой.")


@dp.message_handler(state=Form.subject)
async def process_subject(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['subject'] = message.text

    await Form.next()
    await message.reply("Введите логин.")


@dp.message_handler(state=Form.login)
async def process_login(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    print("Got name")
    async with state.proxy() as data:
        data['login'] = message.text
    await Form.next()
    await message.reply("Введите ваш пароль.")


@dp.message_handler(state=Form.password)
async def process_password(message: types.Message, state: FSMContext):
    """
    Process user name
    """
    async with state.proxy() as data:
        data['password'] = message.text

    await database.execute(f"INSERT INTO teachers(name, subject, login, password) "
                           f"VALUES (:name, :subject, :login, :password)", values={'name': data['name'], 'subject': data['subject'],
                                                                                 'login': data['login'], 'password': data['password']})

    # And send message
    await bot.send_message(
        message.chat.id,
        md.text(
            md.text('Отлично, вы зарегистрированы, ', md.bold(data['name'])),
            md.text('Ваш предмет', md.code(data['subject'])),
            sep='\n',
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
# Finish conversation
    await state.finish()
