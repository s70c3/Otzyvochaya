import asyncio
from random import random

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

@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    await message.reply(
        md.text(
            md.text('Команды:'),
            md.text('Для оценки:', md.bold('/rate')),
            md.text('Для того чтобы узнать обратную связь:' ),
            md.text( md.bold('Как у меня дела?'), 'для ученика'),
            md.text(md.bold('Как меня оценивают?'), 'для учителя'),
            md.text('Оценка предмета придёт к вам по расписанию.'),
            md.text('Тестовые данные: логин и пароль учителя petr, petr'),
            md.text('Тестовые данные: логин и пароль ученика ivan, ivan'),
            sep='\n',
        ),
    )


@dp.message_handler(text_contains='Как у меня дела?')
async def cmd_start(message: types.Message):
    results = await database.fetch_all(query='SELECT * '
                                             'FROM marks_student INNER JOIN students on students_id=students.id '
                                             'WHERE telegram_id=:t_id;',
                                       values={'t_id': message.chat.id})

    d = [[k for k in result.values()] for result in results]
    compliments = []
    negative = []
    wish = []
    for k in d:
        compliments.append(k[3])
        negative.append(k[4])
        wish.append(k[5])

    await message.reply(
        md.text(
            md.text('Комплименты вам, ', md.bold("\n".join(compliments))),
            md.text('Ваши недочёты',  md.bold("\n".join(negative))),
            md.text('Пожелания вам', md.bold("\n".join(wish))),
            sep='\n',
        ),
    )

@dp.message_handler(text_contains='Как меня оценивают?')
async def cmd_start(message: types.Message):
    results = await database.fetch_all(query='SELECT * FROM marks_teacher INNER JOIN teachers on teachers_id=teachers.id '
                                             'WHERE telegram_id=:t_id;',
                                       values={'t_id': message.chat.id})

    d = [[k for k in result.values()] for result in results]
    compliments = []
    negative = []
    wish = []
    for k in d:
        compliments.append(k[3])
        negative.append(k[4])
        wish.append(k[5])

    await message.reply(
        md.text(
            md.text('Комплименты вам: ', md.bold("\n".join(compliments))),
            md.text('Ваши недочёты:',  md.bold("\n".join(negative))),
            md.text('Пожелания вам:', md.bold("\n".join(wish))),
            sep='\n',
        ),
    )


# States
class Work_Form(StatesGroup):
    login_input = State()  # Will be represented in storage as 'Form:name'
    password_input = State()  # Will be represented in storage as 'Form:level'
    select_operation = State()
    # обратная связь по учителю
    select_teacher = State()
    select_compliment_teacher = State()
    select_negative_teacher = State()
    input_wish_for_teacher = State()
    send_for_teacher = State()
    # обратная связь по уроку
    select_student = State()
    select_compliment_student = State()
    select_negative_student = State()
    input_wish_for_student = State()
    send_for_student = State()


    select_subject = State()
    select_subject_mark = State()
    select_content_mark = State()
    send_subject = State()
    wish_subject = State()


@dp.message_handler(commands='rate')
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Conversation's entry point
    """
    # Set state
    print(message.chat.id)
    try:
        user = await database.fetch_one(query='SELECT * '
                                              'FROM teachers '
                                              'WHERE telegram_id = :t_id ',
                                        values={'t_id': message.chat.id})
        d = [k for k in user.values()]
        print('1', d)
        async with state.proxy() as data:
            data['teachers_id'] = d[0]
            data['teacher_name'] = d[3]
            data['subject'] = d[4]
            await Work_Form.select_student.set()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add('Информатика 9')
            await message.reply(
                f"Добро пожаловать, {user['name']}. Оцените учеников? Введите класс и предмет через пробел.", reply_markup=markup)
    except:
        try:
            user = await database.fetch_one(query='SELECT * '
                                                  'FROM students '
                                                  'WHERE telegram_id = :t_id ',
                                            values={'t_id': message.chat.id})
            d = [k for k in user.values()]
            print('2', d)
            async with state.proxy() as data:
                data['student_id'] = d[0]
                data['student_name'] = d[4]
                data['class'] = d[5]
                await Work_Form.select_teacher.set()
                await message.reply(
                    f"Добро пожаловать, {user['name']}. Оцените что-нибудь? Напишите любое слово, если готовы.")
        except:
            await Work_Form.login_input.set()
            await message.reply("Введите ваш логин.")


@dp.message_handler(state=Work_Form.login_input)
async def process_login(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['login'] = message.text

    await Work_Form.next()
    await message.reply("Введите пароль")


@dp.message_handler(state=Work_Form.password_input)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['password'] = message.text
    try:
        user = await database.fetch_one(query='SELECT * '
                                              'FROM teachers '
                                              'WHERE login = :login ',
                                        values={'login': data['login']})
        d = [k for k in user.values()]
        password = d[3]
        async with state.proxy() as data:
            data['teachers_id'] = d[0]
    except:
        await Work_Form.login_input.set()
        await message.reply("Пользователь не найден или пароль не верен. Введите логин заново")

    if data['password'] == password:
        await Work_Form.select_student.set()
        await message.reply(
            f"Добро пожаловать, {user['name']}. Оцените учеников? Введите класс и предмет через пробел.")
    else:
        try:
            user = await database.fetch_one('SELECT * '
                                            'FROM students '
                                            'WHERE login = :login ',
                                            values={'login': data['login']})
            d = [k for k in user.values()]
            async with state.proxy() as data:
                data['student_id'] = d[0]
            password = d[3]
            if data['password'] == password:
                await Work_Form.select_teacher.set()
                await message.reply(
                    f"Добро пожаловать, {user['name']}. Оцените что-нибудь? Напишите любое слово, если готовы.")
            else:
                await Work_Form.login_input.set()
        except:
            await Work_Form.login_input.set()
            await message.reply("Пользователь не найден или пароль не верен. Введите логин заново")


'''
Выбор для учителя
'''

@dp.message_handler(commands='/teacher2student')
@dp.message_handler(state=Work_Form.select_student)
async def select_student(message: types.Message, state: FSMContext):
    subject, level = message.text.split()[:2]
    async with state.proxy() as data:
        data['name'] = message.text
        print(subject, level)
    results = await database.fetch_all(query='SELECT * '
                                             'FROM teachers_has_students INNER JOIN students on students_id=id '
                                             'WHERE teachers_has_students.subject = :subject and students.class=:level',
                                       values={'subject': subject, 'level': int(level)})
    d = [[k for k in result.values()] for result in results]
    print("students", d)
    names = [k[7] for k in d]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(*names)
    await Work_Form.select_compliment_student.set()
    await message.answer('Выберите ученика, которого вы хотите оценить?', reply_markup=markup)


@dp.message_handler(state=Work_Form.select_compliment_student)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['student_name'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Лучший", "Верное направление", "Добрый", "Расстроился", "Ничего")
    await Work_Form.select_negative_student.set()
    await message.answer("Что хорошего можно сказать о работе на уроке?", reply_markup=markup)


@dp.message_handler(state=Work_Form.select_negative_student)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['compliment'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Многовато ошибочек", "Плохое поведение", "Меньше гаджетов", "Агрессивный", "Всё хорошо")
    await Work_Form.input_wish_for_student.set()
    await message.answer("Что плохого можно сказать о работе на уроке?", reply_markup=markup)


@dp.message_handler(state=Work_Form.input_wish_for_student)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['negative'] = message.text

    await Work_Form.send_for_student.set()
    await message.answer("Что вы пожелаете ученику?", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Work_Form.send_for_student)
async def send_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(data['student_name'])
    try:
        user = await database.fetch_one('SELECT * '
                                        'FROM students '
                                        'WHERE name = :name ',
                                        values={'name': data['student_name']})
        print(user)
        student_id = [k for k in user.values()]
        student_id = student_id[0]
        wish = message.text

        await database.execute(f"INSERT INTO marks_student(teachers_id, students_id, compliment, negative, wish) "
                               f"VALUES (:teachers_id, :students_id, :compliment, :negative, :wish)",
                               values={'teachers_id': data['teachers_id'],
                                       'students_id': student_id, 'compliment': data['compliment'],
                                       'negative': data['negative'], 'wish': wish,
                                       })

        await message.answer("Ваша обратная связь записана!")
        await state.finish()
    except:
        await message.answer("Произошла ошибка.")


'''  
Оценка учителя для школьника
'''


@dp.message_handler(commands='/student2teacher')
@dp.message_handler(state=Work_Form.select_teacher)
async def select_student(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    results = await database.fetch_all(query='SELECT * '
                                             'FROM teachers_has_students INNER JOIN teachers on teachers_id=id '
                                             'WHERE students_id = :student_id',
                                       values={'student_id': data['student_id']})
    d = [[k for k in result.values()] for result in results]
    names = [k[7] for k in d]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(*names)
    await Work_Form.select_compliment_teacher.set()
    await message.answer('Выберите учителя, которого вы хотите оценить?', reply_markup=markup)


@dp.message_handler(state=Work_Form.select_compliment_teacher)
async def process_compliment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['teacher_name'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Любимый учитель", "Лучший", "Понятное объяснение")
    await Work_Form.select_negative_teacher.set()
    await message.answer("Что хорошего можно сказать учителю?", reply_markup=markup)


@dp.message_handler(state=Work_Form.select_negative_teacher)
async def process_negative(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['compliment'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Большая загрузка", "Непонятно")
    await Work_Form.input_wish_for_teacher.set()
    await message.answer("Какие недочёты есть у учителя?", reply_markup=markup)


@dp.message_handler(state=Work_Form.input_wish_for_teacher)
async def process_wish(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['negative'] = message.text

    markup = types.ReplyKeyboardRemove()
    await Work_Form.send_for_teacher.set()
    await message.answer("Что вы пожелаете учителю", reply_markup=markup)


@dp.message_handler(state=Work_Form.send_for_teacher)
async def send_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(data['teacher_name'])
    user = await database.fetch_one('SELECT * '
                                    'FROM teachers '
                                    'WHERE name = :name ',
                                    values={'name': data['teacher_name']})
    print(user)
    teacher_id = [k for k in user.values()]
    teacher_id = teacher_id[0]
    wish = message.text

    await database.execute(f"INSERT INTO marks_teacher(teachers_id, students_id, compliment, negative, wish) "
                           f"VALUES (:teachers_id, :students_id, :compliment, :negative, :wish)",
                           values={'teachers_id':teacher_id,
                                   'students_id': data['student_id'], 'compliment': data['compliment'],
                                   'negative': data['negative'], 'wish': wish,
                                   })

    await message.answer("Ваша обратная связь записана!")
    await state.finish()


'''
Оценка предмета
'''


def get_users():
    """
    Return users list
    In this example returns some random ID's
    """
    yield from (90808437)


async def broadcaster() -> int:
    """
    Simple broadcaster
    :return: Count of messages
    """
    count = 0
    try:
        for chat_id in get_users():
            await Work_Form.select_content_mark.set()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            markup.add("5", "4", "3", "2", "1")

            await bot.send_message(
                chat_id,
                md.text(
                    md.text('У вас закончился урок по', random.choice('Информатике', 'Физике', 'Математике')),
                    md.text('Оцените его с точки зрения интереса, пожалуйста.'),
                    sep='\n',
                ),
                reply_markup=markup,
                parse_mode=ParseMode.MARKDOWN,
            )
            await asyncio.sleep(.05)  # 20 messages per second (Limit: 30 messages per second)
            count += 1
    finally:
        print(f"{count} messages successful sent.")
    return count


@dp.message_handler(state=Work_Form.select_content_mark)
async def process_negative(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['interes'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4", "3", "2", "1")
    await Work_Form.input_wish_for_student.set()
    await message.answer("Насколько интересен был контент?", reply_markup=markup)


@dp.message_handler(state=Work_Form.wish_subject)
async def process_wish(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['content'] = message.text

    markup = types.ReplyKeyboardRemove()
    await Work_Form.send_for_student.set()
    await message.answer("Пожелания", reply_markup=markup)


@dp.message_handler(state=Work_Form.send_subject)
async def send_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(data['teacher_name'])
    user = await database.fetch_one('SELECT * '
                                    'FROM teacher '
                                    'WHERE name = :name ',
                                    values={'name': data['teacher_name']})
    print(user)
    teacher_id = [k for k in user.values()]
    teacher_id = teacher_id[0]
    wish = message.text

    await database.execute(f"INSERT INTO marks_subject(teachers_id, students_id, subject, interes, content) "
                           f"VALUES (:teachers_id, :students_id, :subject, :interes, :content)",
                           values={'teachers_id': teacher_id,
                                   'students_id': data['student_id'], 'subject': data['subject'],
                                   'interes': data['interes'], 'content': data['content'],
                                   })

    await message.answer("Ваша обратная связь записана!")
    await state.finish()
