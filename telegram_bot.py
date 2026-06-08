from flask import Flask, request
import requests as http
import os

app = Flask(__name__)

TOKEN = "8868800018:AAGM2HwjfYyDQkMUkUJpag1JrecAXp8ClQw"
API = f"https://api.telegram.org/bot{TOKEN}"

# Coop Details
COOP_NAME = "Hermanus Coop"
COOP_SHAPID = "+27716340281"
COOP_MOMO = "47146617"
MEAL_COST = 35
MEAL_DAY = "Friday"
MEAL_TIME = "12pm - 2pm"

# Simple in-memory store for conversation state
# Format: {chat_id: {"state": "...", "name": "...", "amount": 0}}
user_state = {}

def send(chat_id, text):
    try:
        http.post(f"{API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")

def main_menu(name=""):
    greeting = f"👋 Hi {name}!\n\n" if name else ""
    return (
        f"{greeting}"
        f"🏠 <b>HERMANUS COOP</b>\n\n"
        f"What would you like?\n\n"
        f"1️⃣  🍽️  Share a Meal\n"
        f"2️⃣  💳  Fund My Wallet\n"
        f"3️⃣  💝  Sponsor a Meal\n"
        f"4️⃣  💰  My Balance\n"
        f"5️⃣  ❓  Help\n\n"
        f"<i>Reply with a number</i>"
    )

def fund_menu(amount=None):
    amount_line = f"Amount: <b>R{amount}</b>\n\n" if amount else ""
    return (
        f"💳 <b>FUND MY WALLET</b>\n\n"
        f"{amount_line}"
        f"Choose payment method:\n\n"
        f"1️⃣  📱  PayShap (Bank App)\n"
        f"2️⃣  📲  MoMo USSD\n"
        f"3️⃣  💵  Cash at Office\n\n"
        f"0️⃣  🏠  Back to Menu"
    )

@app.route('/telegram', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data or 'message' not in data:
            return "OK", 200

        msg = data['message']
        chat_id = msg.get('chat', {}).get('id')
        text = msg.get('text', '').strip()

        if not chat_id:
            return "OK", 200

        print(f"Chat: {chat_id} | Text: {text}")

        # Get or create user state
        if chat_id not in user_state:
            user_state[chat_id] = {"state": "new", "name": "", "amount": 0}

        state = user_state[chat_id]["state"]
        name = user_state[chat_id]["name"]

        # ─────────────────────────────────────
        # NEW USER: Ask name
        # ─────────────────────────────────────
        if text == '/start':
            user_state[chat_id]["state"] = "get_name"
            send(chat_id,
                f"👋 <b>Welcome to {COOP_NAME}!</b>\n\n"
                f"I'm your wallet assistant.\n\n"
                f"What's your name?"
            )

        # ─────────────────────────────────────
        # GET NAME
        # ─────────────────────────────────────
        elif state == "get_name":
            user_state[chat_id]["name"] = text.title()
            user_state[chat_id]["state"] = "menu"
            send(chat_id,
                f"✅ Welcome <b>{text.title()}</b>!\n\n"
                f"Your wallet is ready.\n"
                f"Starting balance: <b>R0</b>\n\n"
                + main_menu(text.title())
            )

        # ─────────────────────────────────────
        # BACK TO MENU
        # ─────────────────────────────────────
        elif text == '0' or text.lower() in ['menu', 'back']:
            user_state[chat_id]["state"] = "menu"
            send(chat_id, main_menu(name))

        # ─────────────────────────────────────
        # 1️⃣ SHARE A MEAL
        # ─────────────────────────────────────
        elif text == '1' and state == "menu":
            user_state[chat_id]["state"] = "meal_count"
            send(chat_id,
                f"🍽️ <b>SHARE A MEAL</b>\n\n"
                f"📅 When: Every {MEAL_DAY}\n"
                f"🕐 Time: {MEAL_TIME}\n"
                f"📍 Where: Coop Hall\n"
                f"💰 Cost: R{MEAL_COST} per meal\n\n"
                f"How many meals?\n\n"
                f"1️⃣  1 meal  — R{MEAL_COST}\n"
                f"2️⃣  2 meals — R{MEAL_COST*2}\n"
                f"3️⃣  3 meals — R{MEAL_COST*3}\n"
                f"4️⃣  4 meals — R{MEAL_COST*4}\n\n"
                f"0️⃣  🏠 Back to Menu"
            )

        # MEAL COUNT SELECTED
        elif state == "meal_count" and text in ['1','2','3','4']:
            meals = int(text)
            total = meals * MEAL_COST
            user_state[chat_id]["state"] = "meal_confirm"
            user_state[chat_id]["meals"] = meals
            user_state[chat_id]["total"] = total
            send(chat_id,
                f"🍽️ <b>CONFIRM ORDER</b>\n\n"
                f"Meals: {meals} x R{MEAL_COST}\n"
                f"Total: <b>R{total}</b>\n"
                f"Day: {MEAL_DAY} {MEAL_TIME}\n\n"
                f"1️⃣  ✅ Confirm order\n"
                f"2️⃣  ❌ Cancel\n\n"
                f"0️⃣  🏠 Back to Menu"
            )

        # MEAL CONFIRM
        elif state == "meal_confirm" and text == '1':
            meals = user_state[chat_id].get("meals", 1)
            total = user_state[chat_id].get("total", MEAL_COST)
            user_state[chat_id]["state"] = "menu"
            send(chat_id,
                f"✅ <b>MEALS ORDERED!</b>\n\n"
                f"🍽️ Meals: {meals}\n"
                f"💰 Total: R{total}\n"
                f"📅 {MEAL_DAY} {MEAL_TIME}\n"
                f"📍 Coop Hall\n\n"
                f"See you {MEAL_DAY}! 😊\n\n"
                + main_menu(name)
            )

        elif state == "meal_confirm" and text == '2':
            user_state[chat_id]["state"] = "menu"
            send(chat_id, f"❌ Order cancelled.\n\n" + main_menu(name))

        # ─────────────────────────────────────
        # 2️⃣ FUND MY WALLET
        # ─────────────────────────────────────
        elif text == '2' and state == "menu":
            user_state[chat_id]["state"] = "fund_amount"
            send(chat_id,
                f"💳 <b>FUND MY WALLET</b>\n\n"
                f"How much would you like to add?\n\n"
                f"1️⃣  R50\n"
                f"2️⃣  R100\n"
                f"3️⃣  R200\n"
                f"4️⃣  R500\n"
                f"5️⃣  Other amount\n\n"
                f"0️⃣  🏠 Back to Menu"
            )

        # FUND AMOUNT SELECTED
        elif state == "fund_amount":
            amounts = {'1': 50, '2': 100, '3': 200, '4': 500}
            if text in amounts:
                amount = amounts[text]
                user_state[chat_id]["amount"] = amount
                user_state[chat_id]["state"] = "fund_method"
                send(chat_id, fund_menu(amount))
            elif text == '5':
                user_state[chat_id]["state"] = "fund_custom"
                send(chat_id,
                    f"💳 <b>CUSTOM AMOUNT</b>\n\n"
                    f"Type the amount you want to add:\n"
                    f"(Example: 150)\n\n"
                    f"0️⃣  🏠 Back to Menu"
                )

        # CUSTOM AMOUNT
        elif state == "fund_custom":
            if text.isdigit() and int(text) > 0:
                amount = int(text)
                user_state[chat_id]["amount"] = amount
                user_state[chat_id]["state"] = "fund_method"
                send(chat_id, fund_menu(amount))
            else:
                send(chat_id, "Please type a valid amount (numbers only)\nExample: 150")

        # FUND METHOD SELECTED
        elif state == "fund_method":
            amount = user_state[chat_id].get("amount", 0)

            # PAYSHAP
            if text == '1':
                user_state[chat_id]["state"] = "fund_payshap_confirm"
                send(chat_id,
                    f"📱 <b>PAYSHAP PAYMENT</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"Open your bank app now:\n\n"
                    f"1. Go to: Pay / Send Money\n"
                    f"2. Choose: PayShap\n"
                    f"3. Enter ShapID:\n"
                    f"   <b>{COOP_SHAPID}</b>\n"
                    f"4. Amount: <b>R{amount}</b>\n"
                    f"5. Reference: Your name\n"
                    f"6. Send payment\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"Works with:\n"
                    f"✅ Standard Bank\n"
                    f"✅ Capitec\n"
                    f"✅ FNB\n"
                    f"✅ Absa\n"
                    f"✅ Nedbank\n\n"
                    f"Once paid, reply:\n"
                    f"1️⃣  ✅ I have paid\n"
                    f"2️⃣  ❌ Cancel\n\n"
                    f"0️⃣  🏠 Back to Menu"
                )

            # MOMO USSD
            elif text == '2':
                user_state[chat_id]["state"] = "fund_momo_confirm"
                send(chat_id,
                    f"📲 <b>MOMO USSD PAYMENT</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"Dial this on your phone:\n\n"
                    f"<b>*170*{COOP_MOMO}*{amount}#</b>\n\n"
                    f"Works on ANY phone!\n"
                    f"No internet needed!\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"Not registered for MoMo?\n"
                    f"Dial: <b>*120*151#</b> to register free\n\n"
                    f"Once paid, reply:\n"
                    f"1️⃣  ✅ I have paid\n"
                    f"2️⃣  ❌ Cancel\n\n"
                    f"0️⃣  🏠 Back to Menu"
                )

            # CASH
            elif text == '3':
                user_state[chat_id]["state"] = "menu"
                send(chat_id,
                    f"💵 <b>CASH PAYMENT</b>\n\n"
                    f"Bring R{amount} cash to:\n\n"
                    f"📍 Coop Office\n"
                    f"🕐 Mon-Fri 9am-4pm\n\n"
                    f"We'll add it to your wallet!\n\n"
                    + main_menu(name)
                )

        # PAYMENT CONFIRMED
        elif state in ["fund_payshap_confirm", "fund_momo_confirm"] and text == '1':
            amount = user_state[chat_id].get("amount", 0)
            method = "PayShap" if state == "fund_payshap_confirm" else "MoMo"
            user_state[chat_id]["state"] = "menu"
            send(chat_id,
                f"⏳ <b>PAYMENT RECEIVED!</b>\n\n"
                f"Method: {method}\n"
                f"Amount: R{amount}\n\n"
                f"✅ Your wallet will be updated\n"
                f"within 5 minutes!\n\n"
                f"Questions? Contact operator.\n\n"
                + main_menu(name)
            )

        elif state in ["fund_payshap_confirm", "fund_momo_confirm"] and text == '2':
            user_state[chat_id]["state"] = "menu"
            send(chat_id, f"❌ Payment cancelled.\n\n" + main_menu(name))

        # ─────────────────────────────────────
        # 3️⃣ SPONSOR A MEAL
        # ─────────────────────────────────────
        elif text == '3' and state == "menu":
            user_state[chat_id]["state"] = "sponsor_count"
            send(chat_id,
                f"💝 <b>SPONSOR A MEAL</b>\n\n"
                f"Help a community member\n"
                f"enjoy a Friday meal!\n\n"
                f"How many meals to sponsor?\n\n"
                f"1️⃣  1 meal  — R{MEAL_COST}\n"
                f"2️⃣  2 meals — R{MEAL_COST*2}\n"
                f"3️⃣  5 meals — R{MEAL_COST*5}\n"
                f"4️⃣  10 meals — R{MEAL_COST*10}\n\n"
                f"0️⃣  🏠 Back to Menu"
            )

        # SPONSOR COUNT
        elif state == "sponsor_count" and text in ['1','2','3','4']:
            sponsor_amounts = {'1': 1, '2': 2, '3': 5, '4': 10}
            meals = sponsor_amounts[text]
            total = meals * MEAL_COST
            user_state[chat_id]["state"] = "sponsor_pay"
            user_state[chat_id]["sponsor_total"] = total
            user_state[chat_id]["sponsor_meals"] = meals
            send(chat_id,
                f"💝 <b>SPONSOR PAYMENT</b>\n\n"
                f"Sponsoring: {meals} meal(s)\n"
                f"Amount: <b>R{total}</b>\n\n"
                f"Send via PayShap:\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"ShapID: <b>{COOP_SHAPID}</b>\n"
                f"Amount: <b>R{total}</b>\n"
                f"Reference: <b>SPONSOR</b>\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"Or MoMo:\n"
                f"<b>*170*{COOP_MOMO}*{total}#</b>\n\n"
                f"Once paid:\n"
                f"1️⃣  ✅ I have paid\n"
                f"2️⃣  ❌ Cancel\n\n"
                f"0️⃣  🏠 Back to Menu"
            )

        # SPONSOR CONFIRMED
        elif state == "sponsor_pay" and text == '1':
            meals = user_state[chat_id].get("sponsor_meals", 1)
            total = user_state[chat_id].get("sponsor_total", MEAL_COST)
            user_state[chat_id]["state"] = "menu"
            send(chat_id,
                f"💝 <b>THANK YOU!</b>\n\n"
                f"You've sponsored {meals} meal(s)!\n"
                f"Amount: R{total}\n\n"
                f"🙏 Your generosity feeds\n"
                f"our community!\n\n"
                + main_menu(name)
            )

        elif state == "sponsor_pay" and text == '2':
            user_state[chat_id]["state"] = "menu"
            send(chat_id, f"❌ Sponsorship cancelled.\n\n" + main_menu(name))

        # ─────────────────────────────────────
        # 4️⃣ MY BALANCE
        # ─────────────────────────────────────
        elif text == '4' and state == "menu":
            send(chat_id,
                f"💰 <b>MY BALANCE</b>\n\n"
                f"Name: {name}\n"
                f"Balance: <b>R0</b>\n\n"
                f"<i>To add funds:\n"
                f"Reply 2 to Fund Wallet</i>\n\n"
                + main_menu(name)
            )

        # ─────────────────────────────────────
        # 5️⃣ HELP
        # ─────────────────────────────────────
        elif text == '5' and state == "menu":
            send(chat_id,
                f"❓ <b>HELP & INFO</b>\n\n"
                f"🍽️ <b>Share a Meal:</b>\n"
                f"R{MEAL_COST}/meal every {MEAL_DAY}\n"
                f"at {MEAL_TIME}, Coop Hall\n\n"
                f"💳 <b>Fund Wallet:</b>\n"
                f"PayShap: {COOP_SHAPID}\n"
                f"MoMo: *170*{COOP_MOMO}*AMOUNT#\n"
                f"Cash: At coop office\n\n"
                f"💝 <b>Sponsor a Meal:</b>\n"
                f"Pay for someone else's meal\n"
                f"Same payment methods\n\n"
                f"📞 <b>Problems?</b>\n"
                f"Contact your coop operator\n\n"
                + main_menu(name)
            )

        # ─────────────────────────────────────
        # FALLBACK
        # ─────────────────────────────────────
        else:
            send(chat_id, main_menu(name))

    except Exception as e:
        print(f"Error: {e}")

    return "OK", 200


@app.route('/health', methods=['GET'])
def health():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
