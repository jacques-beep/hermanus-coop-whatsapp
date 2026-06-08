from flask import Flask, request
import requests as http
import os

app = Flask(__name__)

TOKEN = "8868800018:AAGM2HwjfYyDQkMUkUJpag1JrecAXp8ClQw"
API = f"https://api.telegram.org/bot{TOKEN}"

def send(chat_id, text):
    try:
        http.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

@app.route('/telegram', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print(f"Got data: {data}")

        if not data:
            return "OK", 200

        if 'message' not in data:
            return "OK", 200

        msg = data['message']
        chat_id = msg.get('chat', {}).get('id')
        text = msg.get('text', '').strip()

        print(f"Chat: {chat_id} Text: {text}")

        if not chat_id:
            return "OK", 200

        if text == '/start' or text == '0' or text.lower() == 'menu':
            send(chat_id,
                "👋 Welcome to Hermanus Coop!\n\n"
                "Choose:\n\n"
                "1 Fund wallet\n"
                "2 Buy airtime\n"
                "3 Order meals\n"
                "4 Check balance\n"
                "5 Get help"
            )

        elif text == '1':
            send(chat_id,
                "💳 FUND WALLET\n\n"
                "PayShap: +27716340281\n"
                "MoMo: *170*47146617*AMOUNT#\n"
                "Cash: At office\n\n"
                "Reply 0 for menu"
            )

        elif text == '2':
            send(chat_id,
                "📱 BUY AIRTIME\n\n"
                "Type amount:\n"
                "50, 100, 200 or 500\n\n"
                "Reply 0 for menu"
            )

        elif text == '3':
            send(chat_id,
                "🍽️ ORDER MEALS\n\n"
                "Friday 12-2pm\n"
                "R35 per meal\n\n"
                "How many meals?\n"
                "Type: 1, 2, 3 or 4\n\n"
                "Reply 0 for menu"
            )

        elif text == '4':
            send(chat_id,
                "💰 YOUR BALANCE\n\n"
                "Balance: R0\n\n"
                "Reply 0 for menu"
            )

        elif text == '5':
            send(chat_id,
                "❓ HELP\n\n"
                "PayShap: +27716340281\n"
                "MoMo: *170*47146617*AMOUNT#\n"
                "Meals: R35 each Friday\n\n"
                "Reply 0 for menu"
            )

        else:
            send(chat_id,
                "Choose:\n\n"
                "1 Fund wallet\n"
                "2 Buy airtime\n"
                "3 Order meals\n"
                "4 Check balance\n"
                "5 Get help"
            )

    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200


@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
