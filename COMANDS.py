import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from config import TOKEN

engine = create_engine("")

Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Readers(Base):

    __tablename__ = 'warehouse'

    ID_object = Column(Integer, primary_key=True, autoincrement=True)
    Object = Column(String)
    quantity = Column(Integer)
    Time_days = Column(String)

current_inventory = {}


@dp.message(F.text == '/inventory')
async def cmd_inventory(message: Message):
    session = Session()
    try:
        readers = session.query(Readers).all()
        if readers:
            response = "Вот товары на складе:\n\n"
            for reader in readers:
                response += f"Объект: {reader.Object} Количество: {reader.quantity} Время на сборку: {reader.Time_days} дней\n"
        else:
            response = "Нет данных о товарах в системе."
    except Exception as e:
        response = "Произошла ошибка при получении данных."
        print(f"Ошибка: {str(e)}")
    finally:
        session.close()

    await message.answer(response)

class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    phone = Column(String)
    email = Column(String)

@dp.message()
async def cmd_register(message: Message):
    if message.text.startswith("/register"):
        user_id = message.from_user.id
        existing_user = session.query(User).filter_by(user_id=user_id).first()

        if existing_user:
            await message.answer(f'Вы уже зарегистрированы как {existing_user.name}.')
        else:
            data = message.text[len("/register "):].strip().split(",")
            if len(data) == 3:
                name = data[0].strip()
                phone = data[1].strip()
                email = data[2].strip()

                if not re.match(r'^\d+$', phone):
                    await message.answer('Номер телефона должен содержать только цифры.')
                    return

                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                    await message.answer('Пожалуйста, укажите корректный адрес электронной почты.')
                    return

                if name and phone and email:
                    user = User(user_id=user_id, name=name, phone=phone, email=email)
                    try:
                        session.add(user)
                        session.commit()
                        await message.answer(f'Пользователь {name} зарегистрирован с номером {phone} и почтой {email}!')
                    except Exception as e:
                        await message.answer('Произошла ошибка при регистрации. Попробуйте еще раз.')
                        print(f'Ошибка при регистрации пользователя: {e}')
                else:
                    await message.answer('Пожалуйста, укажите корректные данные: имя, номер телефона и почту. '
                                         'Например: /register Никита, 1234567890, example@mail.com')
            else:
                await message.answer('Пожалуйста, укажите имя, номер телефона и почту в формате: '
                                     '/register Имя, Номер телефона, Почта.')
    else:
        await message.answer("Команда не распознана. Попробуйте снова.")



