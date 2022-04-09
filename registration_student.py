
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
    level = State()  # Will be represented in storage as 'Form:subject'


@dp.message_handler(commands='register_student')
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
    print("Got name")
    async with state.proxy() as data:
        data['name'] = message.text
    await Form.next()

    await message.reply("Из какого вы класса? Введите, пожалуйста, только цифру. ")



# # Check age. Age gotta be digit
# @dp.message_handler(lambda message: not message.text.isdigit(), state=Form.age)
# async def process_age_invalid(message: types.Message):
#     """
#     If age is invalid
#     """
#     return await message.reply("Age gotta be a number.\nHow old are you? (digits only)")


@dp.message_handler(lambda message: not message.text.isdigit(), state=Form.subject)
async def process_class_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Вы ввели класс не цифрой. Введите другой.")



@dp.message_handler(state=Form.subject)
async def process_subject(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['class'] = int(message.text)

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()
        await database.execute(f"INSERT INTO students(name, class) "
                               f"VALUES (:name, :class)", values={'name': data['name'], 'class': data['class']})

        # And send message
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Отлично, вы зарегистрированы, ', md.bold(data['name'])),
                md.text('Ваш класс', md.code(data['class'])),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    # Finish conversation
    await state.finish()