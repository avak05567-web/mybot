from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from datetime import datetime
import json
import os

# =====================
# 🔐 CONFIG
# =====================
TOKEN = "8635483359:AAFV1wrBusjFP-Z8CKOFH5I7UonPf4147Co"
ADMIN_ID = 7054785724

DATA_FILE = "data.json"

# =====================
# 💾 DATABASE
# =====================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"balances": {}, "orders": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(DB, f)

DB = load_data()

# =====================
# 🧠 HELPERS
# =====================

def get_balance(uid):
    return DB["balances"].get(str(uid), 0)

def add_balance(uid, amount):
    uid = str(uid)
    DB["balances"][uid] = get_balance(uid) + amount
    save_data()

def add_order(uid, order):
    uid = str(uid)
    DB["orders"].setdefault(uid, [])
    DB["orders"][uid].append(order)
    save_data()

# =====================
# 📋 MENUS
# =====================
menu = ReplyKeyboardMarkup([
    ["🛠 Xizmatlar", "📦 Buyurtmalar"],
    ["💰 Balans", "💳 To‘lov"],
    ["🎁 Bonus"]
], resize_keyboard=True)

services = ReplyKeyboardMarkup([
    ["📸 Instagram"],
    ["🔙 Ortga"]
], resize_keyboard=True)

insta = ReplyKeyboardMarkup([
    ["👥 Obunachi", "❤️ Like"],
    ["🔙 Ortga"]
], resize_keyboard=True)

# =====================
# 🧠 STATE
# =====================
user_state = {}
temp_order = {}
last_bonus = {}

# =====================
# 🚀 START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    DB["balances"].setdefault(str(uid), 0)
    DB["orders"].setdefault(str(uid), [])
    save_data()

    user_state[uid] = None  # reset state

    await update.message.reply_text("👋 Xush kelibsiz PRO SMM bot", reply_markup=menu)

# =====================
# 📩 HANDLER
# =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    username = update.effective_user.username or "user"

    DB["balances"].setdefault(str(uid), 0)
    DB["orders"].setdefault(str(uid), [])

    # 🔙 ORTGA - FIXED
    if text == "🔙 Ortga":
        user_state[uid] = None
        await update.message.reply_text("Menu", reply_markup=menu)
        return

    # 🛠 SERVICES
    if text == "🛠 Xizmatlar":
        user_state[uid] = None
        await update.message.reply_text("Xizmat tanlang", reply_markup=services)

    elif text == "📸 Instagram":
        user_state[uid] = None
        await update.message.reply_text("Instagram xizmatlar", reply_markup=insta)

    elif text == "👥 Obunachi":
        user_state[uid] = "sub"
        await update.message.reply_text("Nechta obunachi? (min 100)")

    elif user_state.get(uid) == "sub":
        try:
            count = int(text)
            if count < 100:
                await update.message.reply_text("Minimum 100")
                return

            price = (count // 100) * 4000

            temp_order[uid] = {"type": "Obunachi", "count": count, "price": price}

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ha", callback_data="yes"),
                 InlineKeyboardButton("Yo‘q", callback_data="no")]
            ])

            await update.message.reply_text(f"{count} obunachi = {price} so‘m", reply_markup=kb)

        except:
            await update.message.reply_text("Raqam kiriting")

        user_state[uid] = None
        return

    elif text == "❤️ Like":
        user_state[uid] = "like"
        await update.message.reply_text("Nechta like?")

    elif user_state.get(uid) == "like":
        try:
            count = int(text)
            if count < 100:
                await update.message.reply_text("Minimum 100")
                return

            price = count * 15

            temp_order[uid] = {"type": "Like", "count": count, "price": price}

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ha", callback_data="yes"),
                 InlineKeyboardButton("Yo‘q", callback_data="no")]
            ])

            await update.message.reply_text(f"{count} like = {price} so‘m", reply_markup=kb)

        except:
            await update.message.reply_text("Raqam kiriting")

        user_state[uid] = None
        return

    # 📦 ORDERS
    elif text == "📦 Buyurtmalar":
        orders = DB["orders"].get(str(uid), [])
        if not orders:
            await update.message.reply_text("Bo‘sh")
        else:
            msg = "Buyurtmalar:\n"
            for o in orders:
                msg += f"{o['type']} {o['count']} = {o['price']}\n"
            await update.message.reply_text(msg)

    # 💰 BALANCE
    elif text == "💰 Balans":
        await update.message.reply_text(f"Balans: {get_balance(uid)} so‘m")

    # 🎁 BONUS
    elif text == "🎁 Bonus":
        today = str(datetime.now().date())
        if last_bonus.get(uid) == today:
            await update.message.reply_text("Bugun olgansan")
        else:
            add_balance(uid, 10)
            last_bonus[uid] = today
            await update.message.reply_text("+10 so‘m bonus")

    # 💳 PAYMENT
    elif text == "💳 To‘lov":
        await update.message.reply_text("Karta: 9860 xxxx xxxx xxxx")

    else:
        await update.message.reply_text("❌ Menyudan tanla")

# =====================
# 🔘 CALLBACK
# =====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    username = query.from_user.username or "user"

    order = temp_order.get(uid)

    if not order:
        await query.edit_message_text("Xatolik")
        return

    if query.data == "yes":
        if get_balance(uid) < order["price"]:
            await query.edit_message_text("Balans yetarli emas")
            return

        add_balance(uid, -order["price"])
        add_order(uid, order)

        await context.bot.send_message(
            ADMIN_ID,
            f"BUYURTMA\n@{username}\n{order}"
        )

        await query.edit_message_text("Qabul qilindi")

    else:
        await query.edit_message_text("Bekor qilindi")

# =====================
# 🚀 RUN
# =====================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button))

print("BOT RUNNING...")
app.run_polling()
