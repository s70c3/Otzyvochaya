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
    #обратная связь по учителю
    select_teacher = State()
    select_compliment_teacher = State()
    select_negative_teacher = State()
    input_wish_for_teacher = State()
    send_for_teacher = State()
   #обратная связь по уроку
    select_student = State()
    select_compliment_student = State()
    select_negative_student = State()
    input_wish_for_student = State()
    send_for_student = State()

    select_subject = State()
    select_subject_mark = State()
    select_content_mark = State()

@dp.message_handler(commands='login')
async def cmd_start(message: types.Message, state: FSMContext):
    """
    Conversation's entry point
    """
    # Set state

    try:
        user = await database.fetch_one(query='SELECT * '
                                              'FROM teachers '
                                              'WHERE telegram_id = :t_id ',
                                        values={'t_id': message.chat.id})
        if user.values():
            d = [k for k in user.values()]
            async with state.proxy() as data:
                data['teachers_id'] = d[0]
                data['name'] = d[3]
                data['subject'] = d[4]
                await Work_Form.select_student.set()
        else:
            user = await database.fetch_one(query='SELECT * '
                                                  'FROM students '
                                                  'WHERE telegram_id = :t_id ',
                                            values={'t_id': message.chat.id})
            d = [k for k in user.values()]
            async with state.proxy() as data:
                data['student_id'] = d[0]
                data['name'] = d[3]
                data['class'] = d[4]
                Work_Form.select_teacher.set()
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
            data['teachers_id']=d[0]
    except:
        await Work_Form.login_input.set()
        await message.reply("Пользователь не найден или пароль не верен. Введите логин заново")

    if data['password']==password:
        await Work_Form.select_student.set()
        await message.reply(f"Добро пожаловать, {user['name']}. Оцените учеников? Введите класс и предмет через пробел.")
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
            if data['password']==password:
                await Work_Form.select_teacher.set()
                await message.reply(f"Добро пожаловать, {user['name']}. Оцените что-нибудь? Напишите любое слово, если готовы.")
            else:
                await Work_Form.login_input.set()
        except:
            await Work_Form.login_input.set()
            await message.reply("Пользователь не найден или пароль не верен. Введите логин заново")

'''
Выбор для учителя
'''

@dp.message_handler(state=Work_Form.select_student)
async def select_student(message: types.Message, state: FSMContext):
    subject, level  = message.text.split()[:2]
    async with state.proxy() as data:
        data['name'] = message.text

    results = await database.fetch_all(query='SELECT * '
                                             'FROM teachers_has_students INNER JOIN students on students_id=id '
                                             'WHERE teachers_has_students.subject = :subject and students.class=:level',
                                       values={'subject': subject, 'level': int(level)})
    d = [[k for k in result.values()] for result in results]
    names = [k[6] for k in d]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(*names)
    await Work_Form.select_compliment_student.set()
    await message.answer('Выберите ученика, которого вы хотите оценить?', reply_markup=markup)


@dp.message_handler(state=Work_Form.select_compliment_student)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['student_name'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4",  "3", "2", "1")
    await Work_Form.select_negative_student.set()
    await message.answer("Что хорошего можно сказать о работе на уроке?", reply_markup=markup)

@dp.message_handler(state=Work_Form.select_negative_student)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['compliment'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4",  "3", "2", "1")
    await Work_Form.input_wish_for_student.set()
    await message.answer("Что плохого можно сказать о работе на уроке?", reply_markup=markup)


@dp.message_handler(state=Work_Form.input_wish_for_student)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['negative'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4",  "3", "2", "1")
    await Work_Form.send_for_student.set()
    await message.answer("Что вы пожелаете ученику?", reply_markup=markup)


@dp.message_handler(state=Work_Form.send_for_student)
async def send_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(data['student_name'])
    user = await database.fetch_one('SELECT * '
                                'FROM students '
                                'WHERE name = :name ',
                                values={'name': data['student_name']})
    print(user)
    student_id = [k for k in user.values()]
    student_id = student_id[0]
    wish = message.text

    await database.execute(f"INSERT INTO marks_student(teachers_id, students_id, compliment, negative, wish) "
                           f"VALUES (:teachers_id, :students_id, :compliment, :negative, :wish)", values={'teachers_id': data['teachers_id'],
                                                                                                          'students_id':student_id, 'compliment': data['compliment'],
                                                                                                          'negative': data['negative'],'wish': wish,
                                                                                                          })

    await message.answer("Ваша обратная связь записана!")
    await state.finish()


'''  
Оценка учителя для школьника
'''

@dp.message_handler(state=Work_Form.select_teacher)
async def select_student(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text

    results = await database.fetch_all(query='SELECT * '
                                             'FROM teachers_has_students INNER JOIN teachers on teachers_id=id '
                                             'WHERE students_id = :student_id',
                                       values={'student_id':data['student_id']})
    d = [[k for k in result.values()] for result in results]
    names = [k[7] for k in d]

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add(*names)
    await Work_Form.select_compliment_teacher.set()
    await message.answer('Выберите учителя, которого вы хотите оценить?', reply_markup=markup)


@dp.message_handler(state=Work_Form.select_compliment_teacher)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['teacher_name'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4",  "3", "2", "1")
    await Work_Form.select_negative_teacher.set()
    await message.answer("Что хорошего можно сказать учителю?", reply_markup=markup)


@dp.message_handler(state=Work_Form.select_negative_teacher)
async def process_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['compliment'] = message.text

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("5", "4",  "3", "2", "1")
    await Work_Form.input_wish_for_student.set()
    await message.answer("Что негативного можно сказать учителю?", reply_markup=markup)


@dp.message_handler(state=Work_Form.input_wish_for_teacher)
async def process_password(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['negative'] = message.text

    markup = types.ReplyKeyboardRemove()
    await Work_Form.send_for_student.set()
    await message.answer("Что вы пожелаете учителю", reply_markup=markup)


@dp.message_handler(state=Work_Form.send_for_teacher)
async def send_feedback(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        print(data['teacher_name'])
    user = await database.fetch_one('SELECT * '
                                'FROM teacher '
                                'WHERE name = :name ',
                                values={'name': data['teacher_name']})
    print(user)
    teacher_id = [k for k in user.values()]
    student_id = teacher_id[0]
    wish = message.text

    await database.execute(f"INSERT INTO marks_teacher(teachers_id, students_id, compliment, negative, wish) "
                           f"VALUES (:teachers_id, :students_id, :compliment, :negative, :wish)", values={'teachers_id': data['teachers_id'],
                                                                                                          'students_id':student_id, 'compliment': data['compliment'],
                                                                                                          'negative': data['negative'],'wish': wish,
                                                                                                          })

    await message.answer("Ваша обратная связь записана!")
    await state.finish()
