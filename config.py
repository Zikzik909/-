import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("")

TOKEN = ''

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



def add_load_order(order):
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

async def create_order(message: Message):
    user_id = message.from_user.id

    data = message.text[len("/orders"):].strip().split(",")
    if len(data) != 3:
        await message.answer(
            "Пожалуйста, укажите ID предмета, количество и дату в формате: /orders ID(Предмета),количество,YYYY-MM-DD")
        return
    try:

        print('1')
        item_id = int(data[0].strip())
        quantity = int(data[1].strip())
        date_str = data[2].strip()
    except ValueError:
        await message.answer("Пожалуйста, убедитесь, что ID и количество являются целыми числами!")
        return

    if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        await message.answer("Пожалуйста, укажите дату в правильном формате: YYYY-MM-DD")
        return
    try:
        order_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        await message.answer("Некорректная дата. Пожалуйста, используйте формат YYYY-MM-DD.")
        return

    item = session.query(Readers).filter_by(ID_object=item_id).one_or_none()

    if item is None:
        await message.answer("Предмет с таким ID не существует.")
        return

    if item.quantity < quantity:
        await message.answer(
            f"Недостаточно предметов '{item.Object}' в наличии. Доступно только {item.quantity} единиц.")
        return

    item.quantity -= quantity

    new_order = Orders(
        user_id=user_id,
        ID_object=item.ID_object,
        object=item.Object,
        quantity=quantity,
        date=order_date
    )

    session.add(new_order)
    session.commit()

    await message.answer(f"Заказ на {quantity} единиц предмета '{item.Object}' на дату {order_date} успешно создан.")


    add_load_order(new_order)
