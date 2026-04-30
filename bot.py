
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import json
import os

# =====================
# CONFIG
# =====================
TOKEN = "8635483359:AAFV1wrBusjFP-Z8CKOFH5I7UonPf4147Co"
ADMIN_ID = 7054785724

DATA_FILE = "data.json"

# =====================
# DB
# =====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"balances": {}, "orders": {}, "referrals": {}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(DB, f)

DB = load_data()

# =====================
# HELPERS
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
# STATE
# =====================
user_state = {}
temp_order = {}
last_bonus = {}

# =====================
# MENU
# =====================
menu = ReplyKeyboardMarkup([
    ["🛠 Xizmatlar", "📦 Buyurtmalar"],
    ["💰 Balans", "💳 To‘lov"],
    ["🎁 Bonus", "🤝 Referral"],
    ["📩 Adminga xabar"]
], resize_keyboard=True)

services = ReplyKeyboardMarkup([
    ["📸 Instagram"],
    ["🔙 Ortga"]
], resize_keyboard=True)

insta = ReplyKeyboardMarkup([
    ["👥 Obunachi", "❤️ Like"],
    ["🔙 Ortga"]
], resize_keyboard=True)

admin_panel = ReplyKeyboardMarkup([
    ["📊 Statistika", "💰 Userga balans"],
    ["🔙 Ortga"]
], resize_keyboard=True)

# =====================
# START + REFERRAL
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)

    DB["balances"].setdefault(uid, 0)
    DB["orders"].setdefault(uid, [])
    DB["referrals"].setdefault(uid, None)

    # referral
    if context.args:
        ref = str(context.args[0])

        if ref != uid and DB["referrals"].get(uid) is None:
            DB["referrals"][uid] = ref
            DB["balances"][ref] = DB["balances"].get(ref, 0) + 100
            save_data()

    await update.message.reply_text("👋 Xush kelibsiz!", reply_markup=menu)

# =====================
# MAIN HANDLER
# =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    username = update.effective_user.username or "user"

    DB["balances"].setdefault(uid, 0)
    DB["orders"].setdefault(uid, [])

    # ================= ADMIN =================
    if text == "/admin" and update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("Admin panel", reply_markup=admin_panel)
        return

    # ================= BONUS =================
    if text == "🎁 Bonus":
        if last_bonus.get(uid):
            await update.message.reply_text("❌ Siz allaqachon bonus olgansiz")
            return

        add_balance(uid, 200)
        last_bonus[uid] = True
        await update.message.reply_text("🎉 200 so‘m bonus oldingiz!")
        return

    # ================= REFERRAL =================
    if text == "🤝 Referral":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={uid}"
        count = list(DB["referrals"].values()).count(uid)

        await update.message.reply_text(
            f"🔗 Referral link:\n{link}\n\n👥 Takliflar: {count}\n💰 100 so‘m har user"
        )
        return

    # ================= BALANCE =================
    if text == "💰 Balans":
        await update.message.reply_text(f"💰 Balans: {get_balance(uid)} so‘m")
        return

    # ================= ADMIN MSG =================
    if text == "📩 Adminga xabar":
        user_state[uid] = "admin_msg"
        await update.message.reply_text("📩 Xabaringizni yozing:")
        return

    if user_state.get(uid) == "admin_msg":
        await context.bot.send_message(
            ADMIN_ID,
            f"📩 XABAR\n@{username}\nID: {uid}\n\n{text}"
        )
        await update.message.reply_text("✔ Yuborildi")
        user_state[uid] = None
        return

    # ================= PAYMENT =================
    if text == "💳 To‘lov":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Chek yuborish", callback_data="send_receipt")]
        ])

        await update.message.reply_text(
            "💳 KARTA:\n9860 1666 5532 3060\n\nTo‘lov qiling va chek yuboring",
            reply_markup=kb
        )
        return

    # ================= RECEIPT MODE =================
    if user_state.get(uid) == "send_receipt":
        await context.bot.send_message(
            ADMIN_ID,
            f"💳 CHEK\n@{username}\nID: {uid}\n\n{text}"
        )
        await update.message.reply_text("✔ Chek yuborildi")
        user_state[uid] = None
        return

    # ================= SERVICES =================
    if text == "🛠 Xizmatlar":
        await update.message.reply_text("Xizmatlar", reply_markup=services)

    elif text == "📸 Instagram":
        await update.message.reply_text("Instagram xizmatlar")

    elif text == "👥 Obunachi":
        user_state[uid] = "sub"
        await update.message.reply_text("Nechta obunachi?")

    elif user_state.get(uid) == "sub":
        try:
            count = int(text)
            price = (count // 100) * 4000

            temp_order[uid] = {"type": "Obunachi", "count": count, "price": price}

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ha", callback_data="yes"),
                 InlineKeyboardButton("Yo‘q", callback_data="no")]
            ])

            await update.message.reply_text(f"{count} = {price} so‘m", reply_markup=kb)
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
            price = count * 15

            temp_order[uid] = {"type": "Like", "count": count, "price": price}

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ha", callback_data="yes"),
                 InlineKeyboardButton("Yo‘q", callback_data="no")]
            ])

            await update.message.reply_text(f"{count} = {price} so‘m", reply_markup=kb)
        except:
            await update.message.reply_text("Raqam kiriting")

        user_state[uid] = None
        return

    elif text == "📦 Buyurtmalar":
        orders = DB["orders"].get(uid, [])
        if not orders:
            await update.message.reply_text("Bo‘sh")
        else:
            msg = "Buyurtmalar:\n"
            for o in orders:
                msg += f"{o['type']} {o['count']} = {o['price']}\n"
            await update.message.reply_text(msg)

    elif text == "🔙 Ortga":
        user_state[uid] = None
        await update.message.reply_text("Menu", reply_markup=menu)

# =====================
# CALLBACK
# =====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = str(query.from_user.id)
    username = query.from_user.username or "user"

    # receipt mode
    if query.data == "send_receipt":
        user_state[uid] = "send_receipt"
        await query.message.reply_text("📩 Chek yuboring")
        return

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
            f"🛒 BUYURTMA\n@{username}\n{order}"
        )

        await query.edit_message_text("Qabul qilindi")

    else:
        await query.edit_message_text("Bekor qilindi")

# =====================
# RUN
# =====================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button))

print("BOT IS RUNNING...")
app.run_polling()
