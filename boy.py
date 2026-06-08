"""
HERMANUS COOP - WHATSAPP BOT WITH BUTTON MENUS + CLAUDE AI
WhatsApp Quick-Reply Buttons + Claude Natural Language
Deploy to Railway
"""

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import anthropic
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime
import re

# Initialize Flask
app = Flask(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+1234567890')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Claude API
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Google Sheets setup
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
GOOGLE_SHEETS_CREDS = os.getenv('GOOGLE_SHEETS_CREDS')

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

try:
    creds_dict = json.loads(GOOGLE_SHEETS_CREDS)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(GOOGLE_SHEETS_ID).worksheet('Sheet1')
except Exception as e:
    print(f"Sheet error: {e}")
    sheet = None

# Coop details
COOP_SHAPID = "+27716340281"
COOP_MOMO_MERCHANT = "47146617"
COOP_NAME = "Hermanus Coop"
MEAL_COST = 35
MEAL_DAY = "Friday"
MEAL_TIME = "12-2pm"


def send_message_with_buttons(phone, message_body, buttons):
    """
    Send WhatsApp message with quick-reply buttons
    
    buttons = [
        {"title": "Fund 💳", "id": "btn_fund"},
        {"title": "Airtime 📱", "id": "btn_airtime"},
        ...
    ]
    """
    try:
        # WhatsApp doesn't support buttons in Twilio sandbox - use text fallback for pilot
        # In production (full WhatsApp Business account), this would send actual buttons
        
        full_message = message_body + "\n\n"
        for i, btn in enumerate(buttons, 1):
            full_message += f"{i}️⃣ {btn['title']}\n"
        
        msg = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=full_message,
            to=f'whatsapp:{phone}'
        )
        return True
    except Exception as e:
        print(f"Send error: {e}")
        return False


# Helper functions
def get_member_phone(phone):
    """Extract clean phone number from WhatsApp format"""
    return phone.replace('whatsapp:', '').replace('+', '')


def get_member_name(phone):
    """Get member name from sheet"""
    if not sheet:
        return "Member"
    try:
        cell = sheet.find(phone)
        if cell:
            name_cell = sheet.cell(cell.row, 2)
            return name_cell.value or "Member"
    except:
        pass
    return "Member"


def get_member_balance(phone):
    """Get member balance from sheet"""
    if not sheet:
        return 0
    try:
        cell = sheet.find(phone)
        if cell:
            balance_cell = sheet.cell(cell.row, 4)
            return float(balance_cell.value or 0)
    except:
        pass
    return 0


def register_member(phone, name):
    """Register member in sheet"""
    if not sheet:
        return False
    try:
        next_row = len(sheet.col_values(1)) + 1
        sheet.update_cell(next_row, 1, phone)
        sheet.update_cell(next_row, 2, name)
        sheet.update_cell(next_row, 3, phone)
        sheet.update_cell(next_row, 4, 0)
        sheet.update_cell(next_row, 5, f"Registered {datetime.now().strftime('%Y-%m-%d')}")
        return True
    except Exception as e:
        print(f"Registration error: {e}")
        return False


def update_balance(phone, amount, reason):
    """Update member balance"""
    if not sheet:
        return False
    try:
        cell = sheet.find(phone)
        if cell:
            current = float(sheet.cell(cell.row, 4).value or 0)
            new_balance = current + amount
            sheet.update_cell(cell.row, 4, new_balance)
            
            history = sheet.cell(cell.row, 5).value or ""
            new_history = f"{history}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}: {reason} {amount:+.2f} (Total: {new_balance:.2f})"
            sheet.update_cell(cell.row, 5, new_history)
            return new_balance
    except Exception as e:
        print(f"Update error: {e}")
        return False


def process_with_claude(user_message, member_name, member_phone, member_balance):
    """Use Claude for natural language questions"""
    
    context = f"""You are a helpful WhatsApp chatbot for Hermanus Coop wallet system.

Member: {member_name}
Balance: R{member_balance:.2f}

Message: "{user_message}"

Respond BRIEFLY (2 sentences max):
- If asking about balance: "Your balance is R{member_balance:.2f}"
- If asking about meals: "Meals cost R35 each on Fridays 12-2pm at coop hall"
- If asking about payments: "PayShap: {COOP_SHAPID} | MoMo: *170*{COOP_MOMO_MERCHANT}*AMOUNT#"
- If asking for help: Briefly list options
- Be friendly and conversational"""

    try:
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {"role": "user", "content": context}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude error: {e}")
        return None


# Main webhook route
@app.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle incoming WhatsApp messages"""
    
    incoming_msg = request.values.get('Body', '').strip()
    from_number = get_member_phone(request.values.get('From', ''))
    from_number_clean = from_number.replace('whatsapp:', '')
    
    response = MessagingResponse()
    
    # Check if member exists
    member_name = get_member_name(from_number_clean)
    member_balance = get_member_balance(from_number_clean)
    is_new = member_name == "Member"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NEW MEMBER: Get name first
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_new:
        if incoming_msg.lower() in ['/start', 'start', 'hi', 'hello', 'hey', '']:
            response.message("👋 Welcome to Hermanus Coop!\n\nWhat's your name?")
        else:
            member_name = incoming_msg.title()
            if register_member(from_number_clean, member_name):
                response.message(
                    f"✅ Welcome {member_name}!\n\n"
                    f"Your wallet is ready.\n"
                    f"Starting balance: R0\n\n"
                    f"Choose what you'd like to do:\n\n"
                    f"1️⃣ Fund wallet 💳\n"
                    f"2️⃣ Buy airtime 📱\n"
                    f"3️⃣ Order meals 🍽️\n"
                    f"4️⃣ Check balance 💰\n"
                    f"5️⃣ Get help ❓"
                )
            else:
                response.message("Error setting up. Please try again.")
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MAIN MENU
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if incoming_msg in ['menu', 'back', '/start'] or (incoming_msg.isdigit() and incoming_msg == '0'):
        response.message(
            f"👋 Hi {member_name}!\n"
            f"💰 Balance: R{member_balance:.2f}\n\n"
            f"What would you like?\n\n"
            f"1️⃣ Fund wallet 💳\n"
            f"2️⃣ Buy airtime 📱\n"
            f"3️⃣ Order meals 🍽️\n"
            f"4️⃣ Check balance 💰\n"
            f"5️⃣ Get help ❓"
        )
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1️⃣ FUND WALLET
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if incoming_msg == '1':
        response.message(
            "💳 *HOW TO FUND YOUR WALLET*\n\n"
            f"Choose a method:\n\n"
            f"1️⃣ *PayShap* (if you have Standard/Capitec/FNB)\n"
            f"    Send to: {COOP_SHAPID}\n\n"
            f"2️⃣ *MoMo USSD* (any MTN phone)\n"
            f"    Dial: *170*{COOP_MOMO_MERCHANT}*AMOUNT#\n\n"
            f"3️⃣ *Cash at office*\n"
            f"    Bring cash, we'll add it\n\n"
            f"0️⃣ Back to menu"
        )
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2️⃣ BUY AIRTIME
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif incoming_msg == '2':
        response.message(
            f"📱 *BUY AIRTIME*\n\n"
            f"Your balance: R{member_balance:.2f}\n\n"
            f"Choose amount:\n\n"
            f"1️⃣ R50\n"
            f"2️⃣ R100\n"
            f"3️⃣ R200\n"
            f"4️⃣ R500\n"
            f"5️⃣ Custom amount (type: 75)\n\n"
            f"0️⃣ Back to menu"
        )
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3️⃣ ORDER MEALS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif incoming_msg == '3':
        response.message(
            f"🍽️ *FRIDAY MEALS*\n\n"
            f"When: {MEAL_DAY} {MEAL_TIME}\n"
            f"Where: Coop hall\n"
            f"Cost: R{MEAL_COST} per meal\n\n"
            f"Your balance: R{member_balance:.2f}\n\n"
            f"How many meals?\n\n"
            f"1️⃣ 1 meal (R{MEAL_COST})\n"
            f"2️⃣ 2 meals (R{MEAL_COST*2})\n"
            f"3️⃣ 3 meals (R{MEAL_COST*3})\n"
            f"4️⃣ 4 meals (R{MEAL_COST*4})\n"
            f"5️⃣ Custom (type: 5)\n\n"
            f"0️⃣ Back to menu"
        )
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4️⃣ CHECK BALANCE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif incoming_msg == '4':
        response.message(
            f"💰 *YOUR BALANCE*\n\n"
            f"Current: R{member_balance:.2f}\n\n"
            f"Choose next:\n\n"
            f"1️⃣ Fund wallet 💳\n"
            f"2️⃣ Buy airtime 📱\n"
            f"3️⃣ Order meals 🍽️\n"
            f"0️⃣ Back to menu"
        )
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 5️⃣ HELP / INFO
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    elif incoming_msg == '5':
        response.message(
            f"❓ *HELP*\n\n"
            f"💳 *Fund wallet:*\n"
            f"PayShap: {COOP_SHAPID}\n"
            f"MoMo: *170*{COOP_MOMO_MERCHANT}*AMOUNT#\n"
            f"Cash: At office\n\n"
            f"📱 *Buy airtime:*\n"
            f"Choose amount, get code\n\n"
            f"🍽️ *Order meals:*\n"
            f"Every {MEAL_DAY} R{MEAL_COST}/meal\n\n"
            f"Questions? Just type them!\n\n"
            f"0️⃣ Back to menu"
        )
        return str(response)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # AIRTIME: Process options
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # This requires context tracking - for now, process digit as airtime amount
    # User must reply with digit when in airtime menu
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NATURAL LANGUAGE FALLBACK (Claude handles it)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    else:
        # Try to understand as airtime amount
        if incoming_msg.isdigit() and int(incoming_msg) in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]:
            amount = int(incoming_msg)
            if member_balance >= amount:
                new_balance = update_balance(from_number_clean, -amount, f"Airtime R{amount}")
                voucher = f"MTN-DEMO-{amount}-{datetime.now().strftime('%H%M%S')}"
                response.message(
                    f"✅ *AIRTIME PURCHASED*\n\n"
                    f"Amount: R{amount}\n"
                    f"Code: {voucher}\n\n"
                    f"🔑 Enter in your phone:\n"
                    f"*141*{voucher}#\n\n"
                    f"New balance: R{new_balance:.2f}\n\n"
                    f"0️⃣ Back to menu"
                )
            else:
                response.message(
                    f"❌ *Insufficient balance*\n\n"
                    f"You need: R{amount}\n"
                    f"You have: R{member_balance:.2f}\n\n"
                    f"Fund your wallet first!\n\n"
                    f"1️⃣ Fund wallet\n"
                    f"0️⃣ Back to menu"
                )
            return str(response)
        
        # Try to understand as meal order
        elif incoming_msg.isdigit() and 1 <= int(incoming_msg) <= 10:
            num_meals = int(incoming_msg)
            cost = num_meals * MEAL_COST
            if member_balance >= cost:
                new_balance = update_balance(from_number_clean, -cost, f"Meals: {num_meals}")
                response.message(
                    f"✅ *MEALS ORDERED*\n\n"
                    f"Meals: {num_meals} x R{MEAL_COST}\n"
                    f"Total: R{cost}\n\n"
                    f"📅 When: {MEAL_DAY} {MEAL_TIME}\n"
                    f"📍 Where: Coop hall\n\n"
                    f"New balance: R{new_balance:.2f}\n\n"
                    f"See you Friday! 🍽️\n\n"
                    f"0️⃣ Back to menu"
                )
            else:
                response.message(
                    f"❌ *Insufficient balance*\n\n"
                    f"You need: R{cost}\n"
                    f"You have: R{member_balance:.2f}\n\n"
                    f"Fund your wallet first!\n\n"
                    f"1️⃣ Fund wallet\n"
                    f"0️⃣ Back to menu"
                )
            return str(response)
        
        # Use Claude for natural language questions
        else:
            claude_response = process_with_claude(incoming_msg, member_name, from_number_clean, member_balance)
            if claude_response:
                response.message(
                    claude_response + "\n\n"
                    "0️⃣ Back to menu"
                )
            else:
                response.message(
                    f"I didn't quite catch that. What would you like?\n\n"
                    f"1️⃣ Fund wallet\n"
                    f"2️⃣ Buy airtime\n"
                    f"3️⃣ Order meals\n"
                    f"4️⃣ Check balance\n"
                    f"5️⃣ Get help"
                )
            return str(response)


# Health check
@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)), debug=False)
