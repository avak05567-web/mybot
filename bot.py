
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import sqlite3
import time

# ================= CONFIG =================
TOKEN = "8635483359:AAFV1wrBusjFP-Z8CKOFH5I7UonPf4147Co"
ADMIN_ID = 7054785724
CARD = "9860 1666 5532 3060"

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id TEXT PRIMARY KEY,
balance INTEGER DEFAULT 0,
ref TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id TEXT,
type TEXT,
count INTEGER,
price INTEGER,
status TEXT DEFAULT 'pending'
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS bonus(
user_id TEXT PRIMARY KEY,
last_time INTEGER
)
""")

conn.commit()

# ================= HELPERS =================
def get_balance(uid):
    cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
    r = cur.fetchone()
    return r[0] if r else 0

def add_balance(uid, amount):
    cur.execute("INSERT OR IGNORE INTO users(id,balance) VALUES(?,0)", (uid,))
    cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, uid))
    conn.commit()

def add_order(uid, t, c, p):
    cur.execute("INSERT INTO orders(user_id,type,count,price,status) VALUES(?,?,?,?,?)",
                (uid, t, c, p, "pending"))
    conn.commit()

def can_bonus(uid):
    cur.execute("SELECT last_time FROM bonus WHERE user_id=?", (uid,))
    r = cur.fetchone()
    return not r or time.time() - r[0] > 86400

# ================= STATE =================
state = {}
temp_order = {}

# ================= MENU =================
menu = ReplyKeyboardMarkup([
    ["🛠 Xizmatlar", "📦 Buyurtmalar"],
    ["💰 Balans", "💳 To‘lov"],
    ["🎁 Bonus", "🤝 Referral"],
    ["🔙 Ortga"]
], resize_keyboard=True)

insta = ReplyKeyboardMarkup([
    ["👥 Obunachi"],
    ["🔙 Ortga"]
], resize_keyboard=True)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    username = update.effective_user.username or "user"

    cur.execute("INSERT OR IGNORE INTO users(id,balance) VALUES(?,0)", (uid,))

    # ---------- REFERRAL FIX ----------
    if context.args:
        ref = str(context.args[0])
        if ref != uid:
            cur.execute("UPDATE users SET ref=? WHERE id=?", (ref, uid))
            add_balance(ref, 100)
            conn.commit()

    await update.message.reply_text("👋 PRO BOT", reply_markup=menu)

# ================= MAIN =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    username = update.effective_user.username or "user"

    # ================= BACK FIX =================
    if text == "🔙 Ortga":
        state[uid] = None
        temp_order.pop(uid, None)
        await update.message.reply_text("🏠 Menu", reply_markup=menu)
        return

    # ================= BALANCE =================
    if text == "💰 Balans":
        await update.message.reply_text(f"💰 {get_balance(uid)} so‘m")
        return

    # ================= BONUS =================
    if text == "🎁 Bonus":
        if not can_bonus(uid):
            await update.message.reply_text("❌ 24h limit")
            return

        add_balance(uid, 100)
        cur.execute("INSERT OR REPLACE INTO bonus VALUES(?,?)", (uid, int(time.time())))
        conn.commit()

        await update.message.reply_text("🎉 +100 so‘m")
        return

    # ================= REFERRAL =================
    if text == "🤝 Referral":
        bot = context.bot.username
        link = f"https://t.me/{bot}?start={uid}"

        cur.execute("SELECT COUNT(*) FROM users WHERE ref=?", (uid,))
        count = cur.fetchone()[0]

        await update.message.reply_text(f"🔗 {link}\n👥 {count} user")
        return

    # ================= PAYMENT =================
    if text == "💳 To‘lov":
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Chek yuborish", callback_data="receipt")]
        ])

        await update.message.reply_text(f"💳 {CARD}", reply_markup=kb)
        return

    # ================= SERVICES =================
    if text == "🛠 Xizmatlar":
        await update.message.reply_text("Xizmatlar", reply_markup=insta)
        return

    # ================= OBUNACHI =================
    if text == "👥 Obunachi":
        state[uid] = "sub"
        await update.message.reply_text("Nechta obunachi?")
        return

    if state.get(uid) == "sub":
        try:
            count = int(text)
            price = count * 10

            temp_order[uid] = ("Obunachi", count, price)

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✔ Ha", callback_data="yes"),
                 InlineKeyboardButton("❌ Yo‘q", callback_data="no")]
            ])

            await update.message.reply_text(f"{count} = {price}", reply_markup=kb)

        except:
            await update.message.reply_text("❌ Raqam yoz")

        state[uid] = None
        return

    # ================= RECEIPT FIX =================
    if state.get(uid) == "receipt":
        await context.bot.send_message(
            ADMIN_ID,
            f"💳 CHEK\n@{username}\n{text}"
        )
        state[uid] = None
        await update.message.reply_text("✔ Yuborildi")
        return

# ================= CALLBACK =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)
    username = q.from_user.username or "user"

    # ---------- RECEIPT ----------
    if q.data == "receipt":
        state[uid] = "receipt"
        await q.message.reply_text("📩 Chek yuboring")
        return

    # ---------- ORDER ----------
    order = temp_order.get(uid)

    if not order:
        await q.edit_message_text("❌ Xato")
        return

    if q.data == "no":
        await q.edit_message_text("❌ Bekor")
        return

    if get_balance(uid) < order[2]:
        await q.edit_message_text("❌ Pul yetarli emas")
        return

    add_balance(uid, -order[2])
    add_order(uid, *order)

    await context.bot.send_message(
        ADMIN_ID,
        f"🛒 BUYURTMA\n@{username}\n{order}"
    )

    await q.edit_message_text("✔ Qabul qilindi")

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button))

print("🚀 100% PRO BOT RUNNING...")
app.run_polling()
