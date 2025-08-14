import threading
from flask import Flask, send_file
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ===== CONFIG =====
TELEGRAM_TOKEN = "8227567922:AAHYI_5qG717YGEhLqr61ox0wgEkeoRrHaU"
ADMIN_ID = 6064485557  # Your Telegram user ID
SECRET_PHRASE = "NewMexicanRat"
BTC_BALANCE = 0.0
PAGE_PATH = "page.html"

# ===== Flask Web Server =====
app = Flask(__name__)

@app.route("/")
def home():
    return send_file(PAGE_PATH)

def run_flask():
    app.run(host="0.0.0.0", port=10000)  # change port if needed for Render

# ===== MENUS =====
def trading_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Balance (BTC)", callback_data="balance")],
        [
            InlineKeyboardButton("➕ Deposit", callback_data="deposit"),
            InlineKeyboardButton("➖ Withdrawal", callback_data="withdrawal")
        ],
        [
            InlineKeyboardButton("📊 Strategy", callback_data="strategy"),
            InlineKeyboardButton("📡 Monitor", callback_data="monitor")
        ],
        [
            InlineKeyboardButton("▶ Start", callback_data="start_trade"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop_trade")
        ],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def admin_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Balance (BTC)", callback_data="balance")],
        [
            InlineKeyboardButton("➕ Deposit", callback_data="deposit_admin"),
            InlineKeyboardButton("➖ Withdrawal", callback_data="withdrawal_admin")
        ],
        [
            InlineKeyboardButton("📊 Strategy", callback_data="strategy"),
            InlineKeyboardButton("📡 Monitor", callback_data="monitor")
        ],
        [
            InlineKeyboardButton("▶ Start", callback_data="start_trade"),
            InlineKeyboardButton("⏹ Stop", callback_data="stop_trade")
        ],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== BOT HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📍 Simulated Trading Menu:",
        reply_markup=trading_menu()
    )

async def secret_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID and update.message.text.strip() == SECRET_PHRASE:
        await update.message.reply_text(
            "🔑 Admin Menu Unlocked:",
            reply_markup=admin_menu()
        )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BTC_BALANCE
    query = update.callback_query
    await query.answer()

    # Regular menu buttons
    if query.data == "balance":
        await query.edit_message_text(f"💰 Current BTC Balance: {BTC_BALANCE:.8f} BTC")
    elif query.data == "deposit":
        BTC_BALANCE += 0.1
        await query.edit_message_text(f"✅ Deposited 0.1 BTC! New Balance: {BTC_BALANCE:.8f} BTC")
    elif query.data == "withdrawal":
        BTC_BALANCE -= 0.1
        await query.edit_message_text(f"✅ Withdrew 0.1 BTC! New Balance: {BTC_BALANCE:.8f} BTC")

    # Admin-only balance injection
    elif query.data == "deposit_admin":
        BTC_BALANCE += 10.0
        await query.edit_message_text(f"💹 Admin Deposit +10 BTC → New Balance: {BTC_BALANCE:.8f} BTC")
    elif query.data == "withdrawal_admin":
        BTC_BALANCE -= 10.0
        await query.edit_message_text(f"💹 Admin Withdrawal -10 BTC → New Balance: {BTC_BALANCE:.8f} BTC")

    # Other functions
    elif query.data == "strategy":
        await query.edit_message_text("📊 Strategy settings coming soon...")
    elif query.data == "monitor":
        await query.edit_message_text("📡 Monitoring system active...")
    elif query.data == "start_trade":
        await query.edit_message_text("▶ Trading simulation started...")
    elif query.data == "stop_trade":
        await query.edit_message_text("⏹ Trading simulation stopped.")
    elif query.data == "help":
        await query.edit_message_text("❓ Help section coming soon...")

# ===== RUN BOTH BOT & FLASK =====
def run_bot():
    app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, secret_trigger))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
