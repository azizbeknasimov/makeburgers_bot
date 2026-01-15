import asyncio
import math
import requests
from collections import defaultdict
from datetime import datetime, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)

# ================== SOZLAMALAR ==================
API_TOKEN = "8301609203:AAFyUSMMI0N_evdYvsNzsj9EQBIcawJeH-8"
ADMIN_ID = 7577230652

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbxR4t0yOYiRUoSLvRroOIpzp0kJ9zffv_BzmbJoBxJBB-Je7Fu5v0b1DfzJ6H0oFNSorA/exec"

SHOP_LAT = 41.354422
SHOP_LON = 69.254689
DELIVERY_RADIUS_KM = 5
DELIVERY_PRICE = 10000

OPEN_TIME = time(9, 0)
CLOSE_TIME = time(23, 0)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

users = {}
daily_stats = {"orders": 0, "total": 0}

# ================== YORDAMCHI ==================
def is_open():
    now = datetime.now().time()
    return OPEN_TIME <= now <= CLOSE_TIME

def distance_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ================== MENU (RASMGA 100% MOS) ==================
MENU = {
    "🌭 Hot Dogs": [
        ("Student Hot-dog 1x", 10000),
        ("Student Hot-dog 2x", 12000),
        ("Canada Hot-dog 1x", 15000),
        ("Canada Hot-dog 2x", 18000),
        ("Big Hot-dog 1x", 20000),
        ("Big Hot-dog 2x", 23000),
        ("Qazi Hot-dog 1x", 25000),
        ("Qazi Hot-dog 2x", 28000),
        ("Big Qazi Hot-dog 1x", 30000),
        ("Big Qazi Hot-dog 2x", 35000),
    ],
    "🍔 Burgers": [
        ("Gamburger", 28000),
        ("Cheeseburger", 33000),
        ("Double Cheese", 43000),
        ("MAKO Burger", 45000),
        ("Chicken Burger", 23000),
        ("KFC Burger", 28000),
        ("Double Chicken Burger", 28000),
        ("Donar Burger", 35000),
    ],
    "🌯 Meats": [
        ("Lavash", 25000),
        ("Big Lavash", 30000),
        ("Lavash with cheese", 30000),
        ("Big Lavash with cheese", 35000),
        ("Shaurma", 30000),
        ("Big Shaurma", 35000),
        ("Donar in plate", 45000),
        ("Haggi", 25000),
        ("Big Haggi", 28000),
        ("Haggi with cheese", 30000),
    ],
    "🍟 Snacks": [
        ("French Fries", 15000),
        ("Village Fries", 15000),
        ("Onion Rings", 13000),
        ("Chicken wings Jack Daniels", 28000),
    ],
    "☕ Hot Drinks": [
        ("Espresso", 10000),
        ("Double Espresso", 12000),
        ("Americano", 15000),
        ("Ice Coffee", 18000),
        ("Cappuccino", 20000),
        ("Latte", 20000),
        ("Glasse", 25000),
        ("Cacao", 10000),
        ("Black tea", 5000),
        ("Green tea", 5000),
        ("Tea with lemon", 10000),
        ("Berry tea", 15000),
        ("Ginger tea with lemon", 20000),
        ("Turkish tea", 20000),
    ],
    "🥤 Cold Drinks": [
        ("Milkshake", 30000),
        ("Pina Colada", 25000),
        ("Mojito", 15000),
        ("Strawberry Mojito", 18000),
        ("Citrus Lemonade", 20000),
        ("Berry Lemonade", 20000),
        ("Ice Tea", 23000),
        ("MAKO Cocktail", 35000),
    ],
}

# ================== KEYBOARDS ==================
lang_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang_uz")],
    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
    [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
])

def main_menu():
    kb = []
    for k in MENU:
        kb.append([InlineKeyboardButton(text=k, callback_data=f"cat_{k}")])
    kb.append([InlineKeyboardButton(text="🛒 Savat", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def products_kb(cat):
    kb = []
    for name, price in MENU[cat]:
        kb.append([
            InlineKeyboardButton(text=f"➕ {name}", callback_data=f"add_{name}"),
            InlineKeyboardButton(text="➖", callback_data=f"remove_{name}")
        ])
    kb.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================== BOT ==================
@dp.message(Command("start"))
async def start(m: types.Message):
    users[m.from_user.id] = {"cart": defaultdict(int)}
    await m.answer("🍔 Make Burgers\nTilni tanlang:", reply_markup=lang_kb)

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def lang(c: types.CallbackQuery):
    if not is_open():
        await c.message.answer("⛔ Ish vaqti: 09:00 – 23:00")
        return
    await c.message.edit_text("📋 Menyudan tanlang:", reply_markup=main_menu())

@dp.callback_query(lambda c: c.data.startswith("cat_"))
async def cat(c: types.CallbackQuery):
    cat_name = c.data.replace("cat_", "")
    await c.message.edit_text(cat_name, reply_markup=products_kb(cat_name))

@dp.callback_query(lambda c: c.data == "back")
async def back(c: types.CallbackQuery):
    await c.message.edit_text("📋 Menyu:", reply_markup=main_menu())

@dp.callback_query(lambda c: c.data.startswith("add_"))
async def add(c: types.CallbackQuery):
    users[c.from_user.id]["cart"][c.data.replace("add_", "")] += 1
    await c.answer("➕ Qo‘shildi")

@dp.callback_query(lambda c: c.data.startswith("remove_"))
async def rem(c: types.CallbackQuery):
    item = c.data.replace("remove_", "")
    if users[c.from_user.id]["cart"][item] > 0:
        users[c.from_user.id]["cart"][item] -= 1
    await c.answer("➖ O‘chirildi")

@dp.callback_query(lambda c: c.data == "cart")
async def cart(c: types.CallbackQuery):
    cart = users[c.from_user.id]["cart"]
    if not any(cart.values()):
        await c.answer("🛒 Savat bo‘sh", show_alert=True)
        return

    text, total = "🛒 Savat:\n", 0
    for k, v in cart.items():
        if v:
            price = next(p for cat in MENU.values() for n, p in cat if n == k)
            total += price * v
            text += f"{k} x{v} = {price*v:,}\n"

    total += DELIVERY_PRICE
    users[c.from_user.id]["total"] = total

    await c.message.answer(
        text + f"\n🚚 Yetkazib berish: {DELIVERY_PRICE:,}\n💰 Jami: {total:,}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📞 Telefon yuborish", request_contact=True)]],
            resize_keyboard=True
        )
    )

@dp.message(lambda m: m.contact)
async def phone(m: types.Message):
    users[m.from_user.id]["phone"] = m.contact.phone_number
    await m.answer(
        "📍 Manzil:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Manzil yuborish", request_location=True)]],
            resize_keyboard=True
        )
    )

@dp.message(lambda m: m.location)
async def loc(m: types.Message):
    dist = distance_km(SHOP_LAT, SHOP_LON, m.location.latitude, m.location.longitude)
    if dist > DELIVERY_RADIUS_KM:
        await m.answer("❌ Yetkazib berish 5 km ichida.")
        return

    users[m.from_user.id]["location"] = f"{m.location.latitude},{m.location.longitude}"

    await m.answer(
        "💳 To‘lov turi:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Naqd", callback_data="pay_cash")],
            [InlineKeyboardButton(text="💳 Karta", callback_data="pay_card")],
            [InlineKeyboardButton(text="💳 Click / Payme", callback_data="pay_online")]
        ])
    )

@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def pay(c: types.CallbackQuery):
    u = users[c.from_user.id]
    order = ", ".join(f"{k} x{v}" for k, v in u["cart"].items() if v)

    requests.post(GOOGLE_SHEETS_URL, json={
        "name": c.from_user.full_name,
        "phone": u["phone"],
        "product": order,
        "payment": c.data,
        "location": u["location"]
    })

    daily_stats["orders"] += 1
    daily_stats["total"] += u["total"]

    await bot.send_message(
        ADMIN_ID,
        f"🆕 BUYURTMA\n👤 {c.from_user.full_name}\n📞 {u['phone']}\n🛒 {order}\n💰 {u['total']:,}\n📍 https://maps.google.com/?q={u['location']}"
    )

    await c.message.answer("✅ Buyurtma qabul qilindi!", reply_markup=ReplyKeyboardRemove())
    users.pop(c.from_user.id)

@dp.message(Command("admin"))
async def admin(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    await m.answer(f"📊 Bugun:\n📦 {daily_stats['orders']}\n💰 {daily_stats['total']:,}")

# ================== RUN ==================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
