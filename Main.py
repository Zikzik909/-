import asyncio
import logging
import re
from datetime import datetime, timedelta

from sqlalchemy.orm import sessionmaker

from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from COMANDS import engine, cmd_register, cmd_inventory

from config import TOKEN, create_order

from Keyboard import kb


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

class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    phone = Column(String)
    email = Column(String)

class Orders(Base):

    __tablename__ = 'orders'

    ID_order = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    ID_object = Column(Integer, ForeignKey('warehouse.ID_object'))
    object = Column(String)
    quantity = Column(Integer)
    date = Column(Date)


class Load(Base):
    __tablename__ = 'load_orders'


    load_id = Column(Integer, primary_key=True, autoincrement=True)
    ID_order = Column(Integer, ForeignKey('orders.ID_order'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    time = Column(Date)
    date_current = Column(Date)
    readiness = Column(String)

current_load_orders = {}


def add_load_order(order):
    logging.info("Starting яяя...")
    warehouse_item = session.query(Readers).filter_by(ID_object=order.ID_object).first()


    if warehouse_item:
        time_days = warehouse_item.Time_days
        date_current = order.date + timedelta(days=order.quantity * time_days)

        load_order = Load(
            ID_order=order.ID_order,
            user_id=order.user_id,
            time=order.date,
            date_current=date_current,
            readiness='Принят'
        )

        session.add(load_order)
        session.commit()


async def send_load_updates_periodically():
    logging.info("Starting load status monitoring...")
    global current_load_orders

    while True:
        session = Session()
        try:
            load_orders = session.query(Load).all()
            new_load_orders = {load.load_id: load.readiness for load in load_orders}

            for load_id, new_status in new_load_orders.items():
                if load_id not in current_load_orders:
                    current_load_orders[load_id] = new_status
                    continue

                if current_load_orders[load_id] != new_status:
                    load_entry = session.query(Load).filter(Load.load_id == load_id).first()
                    user_id = load_entry.user_id

                    old_status = current_load_orders[load_id]
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"Статус заказа {load_id} изменился с '{old_status}' на '{new_status}'."
                    )
                    current_load_orders[load_id] = new_status

            for load_id in list(current_load_orders):
                if load_id not in new_load_orders:
                    del current_load_orders[load_id]

        except Exception as e:
            logging.error(f"Ошибка при отправке уведомлений о статусе заказов: {str(e)}")
        finally:
            session.close()

        await asyncio.sleep(2)



async def show_user_orders(message):
    user_id = message.from_user.id
    orders = session.query(Load).filter(Load.user_id == user_id).all()
    logging.info("Starting status123...")

    if orders == orders:
        await message.answer ("Ваши заказы:\n")
        for order in orders:
            await message.answer (f"Ваш Заказ #: {order.ID_order}\n Статус: {order.readiness}\n Дата готовности: {order.date_current}\n")
    else:
        await message.answer ("У вас нет заказов.")


@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    await message.answer(f"Вас приветствует бот который позволяет вам зарегистрироватся и начать заказывать разные услуги для дальнейшего понимания рекомендуется исаользование команды /info", reply_markup=kb)



@dp.message(F.text == '/info')
async def cmd_inv(message: Message):
    await  message.answer("Для регистраций - /register \nДля просмотря доступных товаров - /inventory \nДля того чтобы сделать заказ - /orders \nДля того чтобы просмотреть статус ваших заказов - /status\n")

@dp.message(F.text == '/inventory')
async def cmd_inv(message: Message):
    logging.info("Starting inventory...")
    await cmd_inventory(message)

@dp.message(F.text.startswith('/orders'))
async def cmd_ord(message: Message):
    if len(message.text) <= len("/orders"):
        await message.answer(
            "Пожалуйста, укажите ID предмета, количество и дату в формате: /orders ID(Предмета),количество,YYYY-MM-DD")
        return
    await  message.answer('fff')
    await create_order(message)

@dp.message(F.text == '/status')
async def cmd_sta(message: Message):
    logging.info("Starting status...")
    await show_user_orders(message)


@dp.message()
async def cmd_reg(message: Message):
    if message.text.startswith("/register"):
        logging.info("Starting register...")
    await cmd_register(message)

async def main():
    logging.basicConfig(level=logging.INFO)

    asyncio.create_task(send_load_updates_periodically())

    await dp.start_polling(bot)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(send_load_updates_periodically())

    try:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
