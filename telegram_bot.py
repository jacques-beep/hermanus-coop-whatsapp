from flask import Flask, request
import requests as req

app = Flask(__name__)

TOKEN = "8868800018:AAGM2HwjfYyDQkMUkUJpag1JrecAXp8ClQw"
API = f"https://api.telegram.org/bot{TOKEN}"

COOP_SHAPID = "+27716340281"
COOP_MOMO = "47146617"
MEAL_COST = 35

def send(chat_id, text):
    req.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text
    })

def main_menu():
    return (
        "🏠 HERMANUS COOP WALLET\n\n"
        "Choose what you'd like:\n\n"
        "1️⃣ Fund wallet 💳\n"
        "2️⃣ Buy airtime 📱\n"
        "3️⃣ Order meals 🍽️\n"
        "4️⃣ Check balance 💰\n"
        "5️⃣ Get help ❓"
    )

@app.route('/telegram', methods=['POST'])
def webhook():
    try:
        data = request.get_json()

        if not data or 'message' not in data:
            return "OK", 200

        msg = data['message']
        chat_id = msg.get('chat', {}).get('id')
        text = msg.get('text', '').strip()

        if not chat_id:
            return "OK", 200

        if text == '/start' or text == '0' or text.lower() == 'menu':
            send(chat_id, 
                "👋 Welcome to Hermanus Coop!\n\n"
                + main_menu()
            )

        elif text == '1':
            send(chat_id,
                "💳 FUND YOUR WALLET\n\n"
                "Option 1 - PayShap:\n"
                f"Send to: {COOP_SHAPID}\n\n"
                "Option 2 - MoMo USSD:\n"
                f"Dial: *170*{COOP_MOMO}*AMOUNT#\n\n"
                "Option 3 - Cash:\n"
                "Bring cash to coop office\n\n"
                "Reply MENU to go back"
            )

        elif text == '2':
            send(chat_id,
                "📱 BUY AIRTIME\n\n"
                "Choose amount:\n\n"
                "Type: 50 for R50\n"
                "Type: 100 for R100\n"
                "Type: 200 for R200\n"
                "Type: 500 for R500\n\n"
                "Reply MENU to go back"
            )

        elif text == '3':
            send(chat_id,
                f"🍽️ ORDER MEALS\n\n"
                f"Every Friday 12-2pm\n"
                f"R{MEAL_COST} per meal\n\n"
                f"1️⃣ 1 meal - R{MEAL_COST}\n"
                f"2️⃣ 2 meals - R{MEAL_COST*2}\n"
                f"3️⃣ 3 meals - R{MEAL_COST*3}\n"
                f"4️⃣ 4 meals - R{MEAL_COST*4}\n\n"
                "Reply with number of meals\n"
                "Reply MENU to go back"
            )

        elif text == '4':
            send(chat_id,
                "💰 YOUR BALANCE\n\n"
                "Balance: R0\n\n"
                "(Google Sheets integration\n"
                "coming in next version)\n\n"
                "Reply MENU to go back"
            )

        elif text == '5':
            send(chat_id,
                "❓ HELP\n\n"
                "💳 Fund wallet:\n"
                f"PayShap: {COOP_SHAPID}\n"
                f"MoMo: *170*{COOP_MOMO}*AMOUNT#\n\n"
                "📱 Airtime:\n"
                "Type amount (50, 100, 200, 500)\n\n"
                "🍽️ Meals:\n"
                f"R{MEAL_COST} each, Fridays 12-2pm\n\n"
                "Reply MENU anytime to go back"
            )

        else:
            send(chat_id,
                f"Got it! ✅\n\n"
                + main_menu()
            )

    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200


@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
