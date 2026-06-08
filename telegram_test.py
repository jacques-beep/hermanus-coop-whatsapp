---CODE START---

from flask import Flask, request
from telegram import Bot
import traceback

app = Flask(__name__)
TELEGRAM_TOKEN = "8868800018:AAGM2HwjfYyDQkMUkUJpag1JrecAXp8ClQw"

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return "OK", 200
        
        msg = data['message']
        chat_id = msg.get('chat', {}).get('id')
        text = msg.get('text', '')
        
        if not chat_id:
            return "OK", 200
        
        bot = Bot(token=TELEGRAM_TOKEN)
        
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="✅ Bot working! Hello from Hermanus Coop!")
        else:
            bot.send_message(chat_id=chat_id, text=f"Echo: {text}")
        
    except Exception as e:
        print(f"ERROR: {traceback.format_exc()}")
    
    return "OK", 200

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)

---CODE END---
