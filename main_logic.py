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

    user = await database.fetch_one(query='SELECT * '
                                          'FROM teachers '
                                          'WHERE login = :login ',
                                    values={'login': data['login']})
    print([k for k in user.values()])
    password = "test"

    if data['password']==password:
        await Work_Form.select_student.set()
        await message.reply(f"Добро пожаловать, {user['name']}. Оцените учеников? Введите класс и предмет через пробел.")
    else:
        user = await database.fetch_one('SELECT * '
                                        'FROM students '
                                        'WHERE login = :login ',
                                        values={'login': data['login']})
        d = [k for k in user.values()]
        print(d)
        password = d[3]
        if data['password']==password:
            await Work_Form.select_operation.set()
            await message.reply(f"Добро пожаловать, {user['name']}. Оцените что-нибудь?")
        else:
            await Work_Form.login_input()
            await message.reply("Пользователь не найден. Введите логин заново")


@dp.message_handler(state=Work_Form.select_student)
async def process_password(message: types.Message, state: FSMContext):
    level, subject = message.text.split()[2]

    results = await database.fetch_one(query='SELECT * '
                                             'FROM teacher_has_students INNER JOIN students on students_id=students.id '
                                             'WHERE teacher_has_students.subject = :subject and students.class=:level',
                                       values={'subject': subject, 'level': level})

    await message.answer([next(result.values()) for result in results])
