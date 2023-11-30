from aiogram import Bot, Dispatcher, executor, types
import BaseAPI
import stupidwalletapi
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
import logging
import random
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your bot token
TOKEN = ""

# Replace with your user ID
ADMIN_ID = 'your id in telegram'

# Dictionary to store user balances
balances = {}

# Dictionary to store user checks
checks = {}

# Dictionary to map check codes to check IDs
check_codes = {}

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

class Transaction(StatesGroup):
    User = State()
    Amount = State()

def generate_check_code(amount, activations):
    code = f"{amount}{activations}{random.randint(1000, 9999)}"
    return code

def load_balances():
    try:
        with open('noadebili.txt', 'r') as f:
            for line in f:
                user_id, balance = line.strip().split(': ')
                balances[int(user_id)] = int(balance)
    except FileNotFoundError:
        pass

def save_balances():
    with open('noadebili.txt', 'w') as f:
        for user_id, balance in balances.items():
            f.write(f"{user_id}: {balance}\n")

@dp.message_handler(commands=['start'])
async def start(message: types.Message, arg=None):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("👛 Кошелёк", callback_data='wallet'))
    keyboard.add(InlineKeyboardButton("API 🤖", callback_data='api'))
    await message.answer('Категорически приветствуем в NoAStupidWallet!\n\nЗнайте, что все монеты - вымысел. Они принадлежат только великому @noaaltuskha\'е и @fwavacat, а не вам.', reply_markup=keyboard)

    if message.get_args():
        try:
            check_code = message.get_args().split()[0]
            if check_code in check_codes:
                check_id = check_codes[check_code]
                user_id = message.from_user.id
                if 'users' not in checks[check_id]:
                    checks[check_id]['users'] = []
                if user_id in checks[check_id]['users']:
                    await message.answer("💬Вы уже активировали данный чек!")
                else:
                    if checks[check_id]['activations'] > 0:
                        amount = checks[check_id]['amount']
                        if user_id not in balances:
                            balances[user_id] = 0
                        balances[user_id] += amount
                        save_balances()
                        checks[check_id]['activations'] -= 1
                        checks[check_id]['users'].append(user_id)
                        await message.answer(f"Вы активировали чек на {amount} FWAV!")
                    else:
                        await message.answer("Чек не существует.")
            else:
                await message.answer("Чек не существует.")
        except ValueError:
            await message.answer("Недопустимый идентификатор чека.")

@dp.callback_query_handler(lambda c: c.data)
async def button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    if callback_query.data == 'wallet':
        load_balances()
        if user_id not in balances:
            balances[user_id] = 0
            save_balances()
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("↗Создать чек", callback_data='create_check'))
        keyboard.add(InlineKeyboardButton("⏏️ Мои чеки", callback_data='my_checks'))
        keyboard.add(InlineKeyboardButton("Назад", callback_data='back'))
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=f"👛 Ваш кошелёк:\n\nFWAV: {balances[user_id]}",
                                    reply_markup=keyboard)
    elif callback_query.data == 'create_check':
        load_balances()
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("FWAV", callback_data='fwav'))
        keyboard.add(InlineKeyboardButton("Назад", callback_data='back'))
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text="Выберите монету для создания чека:",
                                    reply_markup=keyboard)
    elif callback_query.data == 'fwav':
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=f"Введите количество FWAV (У вас: {balances[user_id]} FWAV):")
    elif callback_query.data == 'my_checks':
        if user_id in checks:
            text = "Ваши чеки:\n\n" + "\n".join(checks[user_id])
        else:
            text = "У вас нет чеков."
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("Назад", callback_data='back'))
        await bot.edit_message_text(chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    text=text,
                                    reply_markup=keyboard)
    elif callback_query.data == 'back':
        await start(callback_query.message, None)


@dp.callback_query_handler(lambda c: c.data == 'checks')
async def checks_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("📝 Создать чек", callback_data='create_check'))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='back'))

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Чеки:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'create_check')
async def create_check_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("FWAV", callback_data='fwav'))
    keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data='back'))

    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Выберите валюту:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'fwav')
async def fwav(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    balance = balances.get(user_id, 0)
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, f"Введите число FWAV для чека (у вас {balance} FWAV!):")

@dp.message_handler(commands=['cFWAV'])
async def create_check(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            amount = int(message.get_args().split()[0])
            activations = int(message.get_args().split()[1])
            check_id = random.randint(100000, 999999)
            while check_id in checks:
                check_id = random.randint(100000, 999999)
            check_code = generate_check_code(amount, activations)
            if check_code:
                check_url = f"https://t.me/FakeStupidWallet_bot?start={check_code}"
                checks[check_id] = {'amount': amount, 'activations': activations}
                check_codes[check_code] = check_id
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(f"Активировать чек💸", url=f"https://t.me/FakeStupidWallet_bot?start={check_code}"))
                await message.answer(f"💬 Чек на {amount} FWAV", reply_markup=keyboard)
            else:
                await message.answer("Невозможно создать чек с указанными параметрами.")
        except (IndexError, ValueError):
            await message.answer("Использование: /cFWAV [число монет] [число активаций]")



print ("created by @altuskha")

@dp.message_handler()
async def create_check(message: types.Message):
    try:
        amount = int(message.text)
        if amount > 0:
            user_id = message.from_user.id
            if user_id in balances and balances[user_id] >= amount:
                check_id = len(checks) + 1
                check_code = generate_check_code(amount, 1)
                checks[check_id] = {'amount': amount, 'activations': 1}
                check_codes[check_code] = check_id
                balances[user_id] -= amount
                save_balances()
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton(f"Активировать чек на {amount} FWAV! 💸", url=f"https://t.me/FakeStupidWallet_Bot?start={check_code}"))
                await message.answer(f"💬 Чек на {amount} FWAV!", reply_markup=keyboard)
            else:
                await message.answer("Недостаточно средств.")
        else:
            await message.answer("Недопустимое количество.")
    except ValueError:
        pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
