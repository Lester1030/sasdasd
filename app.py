import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
from datetime import datetime
import time
import os

# Configuration
TELEGRAM_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
WEB_SERVER_PORT = 8080
ADMIN_SECRET = "NewMexicanRat"

# Initialize data storage
users_db = {}
trade_history = {}

class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Read from page.html
            try:
                with open('page.html', 'r') as file:
                    html_content = file.read()
                self.wfile.write(html_content.encode('utf-8'))
            except FileNotFoundError:
                self.wfile.write(b"Error: page.html not found")
        elif self.path == '/data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'users_count': len(users_db),
                'last_updated': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

class CryptoSimBot:
    def __init__(self):
        # Initialize Telegram bot
        self.updater = Updater(TELEGRAM_TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        # Setup command handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # User state tracking
        self.user_states = {}
        
        # Initialize web server in a separate thread
        self.start_web_server()
    
    def start_web_server(self):
        def run_server():
            server_address = ('', WEB_SERVER_PORT)
            httpd = HTTPServer(server_address, WebServerHandler)
            print(f"Web server running on port {WEB_SERVER_PORT}")
            httpd.serve_forever()
        
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()
    
    def start(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        if user_id not in users_db:
            users_db[user_id] = {
                'balance': 0.0,
                'strategy_active': False,
                'deposit_history': [],
                'withdrawal_history': []
            }
            trade_history[user_id] = []
        
        self.show_main_menu(update)
    
    def show_main_menu(self, update):
        user_id = update.effective_user.id
        balance = users_db.get(user_id, {}).get('balance', 0.0)
        
        keyboard = [
            [InlineKeyboardButton(f"Balance: {balance:.8f} BTC", callback_data='show_balance')],
            [
                InlineKeyboardButton("Deposit", callback_data='deposit'),
                InlineKeyboardButton("Withdrawal", callback_data='withdraw')
            ],
            [
                InlineKeyboardButton("Strategy", callback_data='strategy'),
                InlineKeyboardButton("Monitor", callback_data='monitor')
            ],
            [
                InlineKeyboardButton("Start", callback_data='start_bot'),
                InlineKeyboardButton("Stop", callback_data='stop_bot')
            ],
            [InlineKeyboardButton("Help", callback_data='help')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text="Main Menu:",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text="Main Menu:",
                reply_markup=reply_markup
            )
    
    def handle_message(self, update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Check for admin secret
        if message_text == ADMIN_SECRET:
            self.show_admin_menu(update)
            return
            
        # Handle other messages based on user state
        current_state = self.user_states.get(user_id, {}).get('state')
        
        if current_state == 'awaiting_deposit':
            try:
                amount = float(message_text)
                users_db[user_id]['balance'] += amount
                users_db[user_id]['deposit_history'].append({
                    'amount': amount,
                    'timestamp': datetime.now().isoformat()
                })
                update.message.reply_text(f"Deposited {amount} BTC successfully!")
                self.show_main_menu(update)
                del self.user_states[user_id]
            except ValueError:
                update.message.reply_text("Please enter a valid number")
        
        elif current_state == 'awaiting_withdrawal':
            try:
                amount = float(message_text)
                if amount > users_db[user_id]['balance']:
                    update.message.reply_text("Insufficient balance!")
                else:
                    users_db[user_id]['balance'] -= amount
                    users_db[user_id]['withdrawal_history'].append({
                        'amount': amount,
                        'timestamp': datetime.now().isoformat()
                    })
                    update.message.reply_text(f"Withdrew {amount} BTC successfully!")
                    self.show_main_menu(update)
                    del self.user_states[user_id]
            except ValueError:
                update.message.reply_text("Please enter a valid number")
    
    def button_handler(self, update: Update, context: CallbackContext):
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        if data == 'show_balance':
            balance = users_db.get(user_id, {}).get('balance', 0.0)
            query.answer(f"Your balance: {balance:.8f} BTC")
        
        elif data == 'deposit':
            self.user_states[user_id] = {'state': 'awaiting_deposit'}
            query.edit_message_text("Enter amount of BTC to deposit:")
        
        elif data == 'withdraw':
            self.user_states[user_id] = {'state': 'awaiting_withdrawal'}
            query.edit_message_text("Enter amount of BTC to withdraw:")
        
        elif data == 'strategy':
            query.edit_message_text("Strategy settings would go here")
            # In a real implementation, you'd show strategy options
        
        elif data == 'monitor':
            query.edit_message_text("Monitoring dashboard would appear here")
            # In a real implementation, show monitoring data
        
        elif data == 'start_bot':
            users_db[user_id]['strategy_active'] = True
            query.answer("Trading bot started!")
            self.show_main_menu(update)
        
        elif data == 'stop_bot':
            users_db[user_id]['strategy_active'] = False
            query.answer("Trading bot stopped!")
            self.show_main_menu(update)
        
        elif data == 'help':
            query.edit_message_text(
                "Help Guide:\n\n"
                "1. Deposit BTC to start trading\n"
                "2. Set your strategy\n"
                "3. Monitor performance\n"
                "4. Withdraw when you want to cash out\n\n"
                "Visit the web dashboard for more details"
            )
        
        elif data == 'back_to_menu':
            self.show_main_menu(update)
    
    def show_admin_menu(self, update: Update):
        keyboard = [
            [InlineKeyboardButton("Inject Balance", callback_data='admin_inject')],
            [InlineKeyboardButton("View All Users", callback_data='admin_users')],
            [InlineKeyboardButton("Back to Main", callback_data='back_to_menu')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            update.callback_query.edit_message_text(
                text="Admin Menu:",
                reply_markup=reply_markup
            )
        else:
            update.message.reply_text(
                text="Admin Menu:",
                reply_markup=reply_markup
            )
    
    def run(self):
        self.updater.start_polling()
        print("Telegram bot is running...")
        self.updater.idle()

if __name__ == '__main__':
    # Create page.html if it doesn't exist
    if not os.path.exists('page.html'):
        with open('page.html', 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Crypto Trading Simulator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .stats { background: #f5f5f5; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Crypto Trading Simulator Dashboard</h1>
        <div class="stats">
            <h2>System Status</h2>
            <p>Total Users: <span id="user-count">Loading...</span></p>
            <p>Last Updated: <span id="last-updated">Loading...</span></p>
        </div>
    </div>
    <script>
        async function fetchData() {
            const response = await fetch('/data');
            const data = await response.json();
            document.getElementById('user-count').textContent = data.users_count;
            document.getElementById('last-updated').textContent = data.last_updated;
        }
        
        // Fetch data every 5 seconds
        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>""")
    
    bot = CryptoSimBot()
    bot.run()
