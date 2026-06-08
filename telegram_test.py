from flask import Flask, request
from telegram import Bot

app = Flask(__name__)
TELEGRAM_TOKEN = "8868800018:AAGM2HwjfYyDQkMUkUJpag1JrecAXp8ClQw"
bot = Bot(token=TELEGRAM_TOKEN)

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json()
        if not data:
            return "OK", 200
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id or not text:
            return "OK", 200
        
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="👋 Welcome to Hermanus Coop!")
        elif text == '4':
            bot.send_message(chat_id=chat_id, text="💰 Your balance: R0")
        else:
            bot.send_message(chat_id=chat_id, text=f"You said: {text}")
    except Exception as e:
        print(f"Error: {e}")
    return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)