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
    input_wish_for_teacher = State()
    select_subject = State()
    select_subject_mark = State()
    select_content_mark = State()
    select_student = State()
    select_mark = State()
    input_wish_for_student = State()
    send_for_student = State()


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


    user = await database.fetch_one(query='SELECT * '
                                          'FROM teachers '
                                          'WHERE login = :login ',
                                    values={'login': data['login']})
    d = [k for k in user.values()]
    password = d[3]
    async with state.proxy() as data:
        data['password'] = message.text
        data['teachers_id']=d[0]

    if data['password']==password:
        await Work_Form.select_student.set()
        await message.reply(f"Добро пожаловать, {user['name']}. Оцените учеников? Введите класс и предмет через пробел.")
    else:
        user = await database.fetch_one('SELECT * '
                                        'FROM students '
                                        'WHERE login = :login ',
                                        values={'login': data['login']})
        d = [k for k in user.values()]
        password = d[3]
        if data['password']==password:
            await Work_Form.select_operation.set()
            await message.reply(f"Добро пожаловать, {user['name']}. Оцените что-нибудь?")
        else:
            await Work_Form.login_input.set()
            await message.reply("Пользователь не найден. Введите логин заново")


@dp.message_handler(state=Work_Form.select_student)
async def process_password(message: types.Message, state: FSMContext):
    level, subject = message.text.split()[:2]
    async with state.proxy() as data:
        data['name'] = message.text

    results = await database.fetch_one(query='SELECT * '
                                             'FROM teachers_has_students INNER JOIN students on students_id=students.id '
                                             'WHERE teachers_has_students.subject = :subject and students.class=:level',
                                       values={'subject': subject, 'level': int(level)})
    d = [next(result.values()) for result in results]
    print(d)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(d)
    await Work_Form.select_mark.set()
    await message.answer('Выберите ученика, которого вы хотите оценить?', reply_markup=markup)


@dp.message_handler(state=Work_Form.select_mark)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['student_name'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4",  "3", "2", "1")
    await Work_Form.send_for_student.set()
    await message.answer("Какую оценку вы поставите ему за работу на уроке?", reply_markup=markup)


@dp.message_handler(state=Work_Form.send_for_student)
async def process_password(message: types.Message, state: FSMContext):

    wish = message.text


    await database.execute(f"INSERT INTO marks_student(teachers_id, students_id, compliment, negative, wish) "
                           f"VALUES (:name, :subject, :login, :password)", values={'name': data['name'], 'subject': data['subject'],
                                                                                 'login': data['login'], 'password': data['password']})

    await Work_Form.send_for_student.set()
    await message.answer("Напишите готово для отправки")
