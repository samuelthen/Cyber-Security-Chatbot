import openai
import os
from dotenv import load_dotenv
from flask import Flask, request
from twilio.rest import Client

# Load environment variables
load_dotenv()

# OpenAI setup
openai_api_key = os.getenv('OPENAI_API_KEY')

# Twilio setup
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

if not all([openai_api_key, account_sid, auth_token, twilio_whatsapp_number]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

twilio_client = Client(account_sid, auth_token)

app = Flask(__name__)

# Instantiate the OpenAI client
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def create_cybersecurity_prompt(user_message):
    return f"Pertanyaan tentang keamanan siber: {user_message}"

def generate_response(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Anda adalah konsultan ahli keamanan siber."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50  # Adjust max tokens as needed
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return "Maaf, saya tidak dapat memberikan jawaban yang tepat. Silakan coba pertanyaan lain tentang keamanan siber."

def send_whatsapp_message(to_number, message_body):
    try:
        message = twilio_client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_number}',
            body=message_body,
            to=to_number
        )
        return message.sid
    except Exception as e:
        print(f"Error sending WhatsApp message: {str(e)}")
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From')
    
    print(f"Received message: {incoming_msg}")
    
    if incoming_msg:
        prompt = create_cybersecurity_prompt(incoming_msg)
        print(f"Generated prompt: {prompt}")
        
        response_text = generate_response(prompt)
        print(f"Generated response: {response_text}")
    else:
        response_text = "Maaf, saya tidak mengerti. Tolong ulangi pertanyaan Anda tentang keamanan siber."
    
    message_sid = send_whatsapp_message(sender, response_text)
    if message_sid:
        print(f"Message sent successfully. SID: {message_sid}")
    else:
        print("Failed to send message")
    
    return '', 204

@app.route('/', methods=['GET'])
def home():
    return "Cybersecurity Chatbot is running!", 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
