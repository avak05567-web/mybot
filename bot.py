
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from datetime import datetime

# 🔐 SETTINGS
TOKEN = "8635483359:AAFV1wrBusjFP-Z8CKOFH5I7UonPf4147Co"
ADMIN_ID = 7054785724

# 🧠 DATABASE
balances = {}
orders = {}
user_state = {}
temp_order = {}
last_bonus = {}
ref_used = set()

# 📋 MENU
menu = ReplyKeyboardMarkup([
    ["🛠 Xizmatlar", "📦 Buyurtmalar"],
    ["🎁 Bonus", "🤝 Referral"],
    ["💰 Balans", "💳 To‘lov"]
], resize_keyboard=True)

services = ReplyKeyboardMarkup([
    ["📸 Instagram", "🔙 Ortga"]
], resize_keyboard=True)

insta = ReplyKeyboardMarkup([
    ["👥 Obunachi", "❤️ Like"],
    ["🔙 Ortga"]
], resize_keyboard=True)

# 🚀 START + REFERRAL
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    balances.setdefault(uid, 0)
    orders.setdefault(uid, [])

    # 🤝 referral
    if context.args:
        ref_id = int(context.args[0])

        if ref_id != uid and uid not in ref_used:
            balances[ref_id] = balances.get(ref_id, 0) + 100
            ref_used.add(uid)

    await update.message.reply_text("👋 Xush kelibsiz SMM botga!", reply_markup=menu)

# 📩 MAIN HANDLER
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    username = update.effective_user.username or "user"

    balances.setdefault(uid, 0)
    orders.setdefault(uid, [])

    # 🛠 XIZMATLAR
    if text == "🛠 Xizmatlar":
        await update.message.reply_text("📋 Xizmat tanlang:", reply_markup=services)

    elif text == "📸 Instagram":
        await update.message.reply_text("📸 Instagram:", reply_markup=insta)

    elif text == "👥 Obunachi":
        user_state[uid] = "sub"
        await update.message.reply_text("👥 Nechta obunachi kerak? (min 100)")

    elif user_state.get(uid) == "sub":
        try:
            count = int(text)

            if count < 100:
                await update.message.reply_text("❌ Minimum 100")
                return

            price = (count // 100) * 4000

            temp_order[uid] = {
                "type": "Obunachi",
                "count": count,
                "price": price
            }

            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Ha", callback_data="yes"),
                    InlineKeyboardButton("❌ Yo‘q", callback_data="no")
                ]
            ])

            await update.message.reply_text(
                f"📦 {count} obunachi\n💰 {price} so‘m\n\nTasdiqlaysizmi?",
                reply_markup=kb
            )

        except:
            await update.message.reply_text("❌ Raqam kiriting")

    elif text == "❤️ Like":
        user_state[uid] = "like"
        await update.message.reply_text("❤️ Nechta like? (min 100)")

    elif user_state.get(uid) == "like":
        try:
            count = int(text)

            if count < 100:
                await update.message.reply_text("❌ Minimum 100")
                return

            price = count * 15

            temp_order[uid] = {
                "type": "Like",
                "count": count,
                "price": price
            }

            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Ha", callback_data="yes"),
                    InlineKeyboardButton("❌ Yo‘q", callback_data="no")
                ]
            ])

            await update.message.reply_text(
                f"📦 {count} like\n💰 {price} so‘m\n\nTasdiqlaysizmi?",
                reply_markup=kb
            )

        except:
            await update.message.reply_text("❌ Raqam kiriting")

    # 📦 BUYURTMALAR
    elif text == "📦 Buyurtmalar":
        if not orders[uid]:
            await update.message.reply_text("📭 Hech narsa yo‘q")
        else:
            msg = "📦 Buyurtmalar:\n\n"
            for o in orders[uid]:
                msg += f"{o['type']} - {o['count']} - {o['price']} so‘m\n"
            await update.message.reply_text(msg)

    # 💰 BALANS
    elif text == "💰 Balans":
        await update.message.reply_text(f"💰 {balances[uid]} so‘m")

    # 🎁 BONUS
    elif text == "🎁 Bonus":
        today = str(datetime.now().date())

        if last_bonus.get(uid) == today:
            await update.message.reply_text("❌ Bugun olding")
        else:
            balances[uid] += 10
            last_bonus[uid] = today
            await update.message.reply_text("🎉 +10 like")

    # 💳 TO‘LOV
    elif text == "💳 To‘lov":
        await update.message.reply_text(
"""💳 KARTA:
9860 1666 5532 3060

📩 Chekni @saparov_anvarbek ga yuboring"""
        )

    # 🤝 REFERRAL
    elif text == "🤝 Referral":
        bot_username = context.bot.username
        link = f"https://t.me/{bot_username}?start={uid}"

        await update.message.reply_text(
f"""🤝 Referral link:

{link}

💰 +100 so‘m har user"""
        )

    elif text == "🔙 Ortga":
        await update.message.reply_text("Menu", reply_markup=menu)

    else:
        await update.message.reply_text("❌ Menyudan tanla")

# 🔘 INLINE BUTTON
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    username = query.from_user.username or "user"

    if query.data == "yes":
        order = temp_order.get(uid)

        balances[uid] -= order["price"]
        orders[uid].append(order)

        await context.bot.send_message(
            ADMIN_ID,
            f"""📦 BUYURTMA

👤 @{username}
🆔 {uid}
📌 {order['type']}
🔢 {order['count']}
💰 {order['price']}"""
        )

        await query.edit_message_text("✅ Buyurtma qabul qilindi!")

    else:
        await query.edit_message_text("❌ Bekor qilindi")

# 🚀 RUN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button))

print("Bot ishlayapti...")
app.run_polling()
