import threading
from flask import Flask, send_file
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ===== CONFIG =====
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
ADMIN_ID = 123456789  # Your Telegram user ID
SECRET_PHRASE = "NewMexicanRat"
BTC_BALANCE = 0.0
PAGE_PATH = "page.html"

# ===== Flask Web Server =====
app = Flask(__name__)

@app.route("/")
def home():
    return send_file(PAGE_PATH)

def run_flask():
    app.run(host="0.0.0.0", port=10000)  # Render uses assigned port, set env var if needed

# ===== Telegram Bot Handlers =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the Simulated Crypto Trading Bot!")

async def secret_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BTC_BALANCE
    if update.message.from_user.id == ADMIN_ID and update.message.text.strip() == SECRET_PHRASE:
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
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("📍 Admin Menu:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BTC_BALANCE
    query = update.callback_query
    await query.answer()

    if query.data == "balance":
        await query.edit_message_text(f"💰 Current BTC Balance: {BTC_BALANCE:.8f} BTC")
    elif query.data == "deposit":
        BTC_BALANCE += 1.0  # Example deposit
        await query.edit_message_text(f"✅ Deposited! New Balance: {BTC_BALANCE:.8f} BTC")
    elif query.data == "withdrawal":
        BTC_BALANCE -= 1.0  # Example withdrawal
        await query.edit_message_text(f"✅ Withdrawn! New Balance: {BTC_BALANCE:.8f} BTC")
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

# ===== Run Bot & Flask Together =====
def run_bot():
    app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, secret_trigger))
    app_bot.add_handler(CallbackQueryHandler(button_click))
    app_bot.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
