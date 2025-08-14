import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
from datetime import datetime
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
ADMIN_SECRET = os.getenv('ADMIN_SECRET', 'NewMexicanRat')
WEB_PORT = int(os.getenv('PORT', '8080'))  # Render provides PORT
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # For production webhook

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'OK',
                'time': datetime.now().isoformat(),
                'users': len(users_db)
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open('page.html', 'r') as file:
                    self.wfile.write(file.read().encode('utf-8'))
            except FileNotFoundError:
                self.wfile.write(b"Dashboard will be available after first request")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

class CryptoSimBot:
    def __init__(self):
        self.users_db = {}
        self.trade_history = {}
        self.user_states = {}
        
        # Initialize Telegram bot
        self.updater = Updater(TELEGRAM_TOKEN, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        # Register handlers
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Error handler
        self.dispatcher.add_error_handler(self.error_handler)
        
        # Web server setup
        self.server = HTTPServer(('0.0.0.0', WEB_PORT), HealthCheckHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
    
    def start_webhook(self):
        """Configure webhook for production"""
        if WEBHOOK_URL:
            self.updater.start_webhook(
                listen="0.0.0.0",
                port=WEB_PORT,
                url_path=TELEGRAM_TOKEN,
                webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_TOKEN}"
            )
            logger.info("Webhook configured")
        else:
            self.updater.start_polling()
            logger.info("Using polling mode")
    
    def run(self):
        """Start both bot and web server"""
        self.server_thread.start()
        logger.info(f"Web server started on port {WEB_PORT}")
        
        self.start_webhook()
        logger.info("Bot started")
        
        # Handle shutdown signals
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        
        # Keep main thread alive
        while True:
            time.sleep(1)
    
    def shutdown(self, signum, frame):
        """Clean shutdown for Render"""
        logger.info("Shutting down gracefully...")
        self.updater.stop()
        self.server.shutdown()
        self.server.server_close()
        logger.info("Server stopped")
        exit(0)
    
    # ... [Rest of your bot methods from previous implementation] ...
    
    def error_handler(self, update: Update, context: CallbackContext):
        """Log errors"""
        logger.error(f"Update {update} caused error {context.error}")

def create_default_html():
    """Create default page.html if not exists"""
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
        <p>This bot is running on Render.com</p>
        <div class="stats">
            <h2>System Status</h2>
            <p>Total Users: <span id="user-count">Loading...</span></p>
            <p>Last Updated: <span id="last-updated">Loading...</span></p>
        </div>
    </div>
    <script>
        async function fetchData() {
            try {
                const response = await fetch('/health');
                const data = await response.json();
                document.getElementById('user-count').textContent = data.users;
                document.getElementById('last-updated').textContent = data.time;
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        }
        fetchData();
        setInterval(fetchData, 5000);
    </script>
</body>
</html>""")

if __name__ == '__main__':
    create_default_html()
    bot = CryptoSimBot()
    bot.run()
