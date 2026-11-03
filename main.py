from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# معلومات البوت الخاصة بك
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8175556330:AAGP0GZf10h0H_Fc10NJAbKJpP-zOH0xFwM')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '658962728')

@app.route('/send-to-bot', methods=['POST'])
def send_to_bot():
    try:
        # استقبال البيانات من تطبيقك
        data = request.json
        message_text = data.get('message', 'رسالة بدون نص')
        
        # إرسال الرسالة إلى تليجرام
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": f"📱 من التطبيق:\n{message_text}"
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "تم الإرسال للبوت"})
        else:
            return jsonify({"status": "error", "message": "فشل الإرسال"}), 500
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    return "الخادم يعمل بنجاح! ✅"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
