import os
from dotenv import load_dotenv
from flask import Flask, request
from twilio.rest import Client
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Load environment variables
load_dotenv()

# Twilio setup
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')

if not all([account_sid, auth_token, twilio_whatsapp_number]):
    raise ValueError("Missing required environment variables. Please check your .env file.")

client = Client(account_sid, auth_token)

# Load a different pre-trained model for text generation
model_name = "gpt2"  # Use a model suitable for text generation
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)
generator = pipeline('text-generation', model=model, tokenizer=tokenizer)

app = Flask(__name__)

def create_cybersecurity_prompt(user_message):
    return f"""
Pertanyaan tentang keamanan siber: {user_message}

Jawaban yang informatif dan relevan tentang keamanan siber:
1. """

def generate_response(prompt):
    response = generator(prompt, max_length=200, num_return_sequences=1, temperature=0.7, do_sample=True, truncation=True)
    response_text = response[0]['generated_text'].split("1. ")[-1].strip()
    
    # Basic post-processing
    sentences = response_text.split('.')
    unique_sentences = list(dict.fromkeys(sentences))  # Remove duplicates
    cleaned_response = '. '.join(sentence.strip() for sentence in unique_sentences if len(sentence.strip()) > 10)
    
    return cleaned_response if cleaned_response else "Maaf, saya tidak dapat memberikan jawaban yang tepat. Silakan coba pertanyaan lain tentang keamanan siber."

def send_whatsapp_message(to_number, message_body):
    try:
        message = client.messages.create(
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
