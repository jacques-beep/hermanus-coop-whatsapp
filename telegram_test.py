from flask import Flask, request
from telegram import Bot
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

TELEGRAM_TOKEN = "8868800018:AAGM2HwjfYyDQkMUkUJpag1JrecAXp8ClQw"
bot = Bot(token=TELEGRAM_TOKEN)

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    try:
        update = request.get_json()
        print(f"Received: {update}")
        
        if 'message' not in update:
            return "OK", 200
        
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        print(f"Chat ID: {chat_id}, Text: {text}")
        
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="✅ Bot is working! Hello from Hermanus Coop!")
        else:
            bot.send_message(chat_id=chat_id, text=f"You sent: {text}")
        
        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
