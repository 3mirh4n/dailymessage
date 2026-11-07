import os
import time
import requests
import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask

# ==========================================
# 1. BOT BİLGİLERİ (Kendi bilgilerini buraya yaz)
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# ==========================================
# 2. RENDER UYKU ENGELLENME SUNUCUSU
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "7/24 Etkileşimli Asistan Aktif!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web_server, daemon=True).start()


# ==========================================
# 3. VERİ ÇEKME FONKSİYONLARI (Aynı kaldı)
# ==========================================
def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=50.06&longitude=19.94&current_weather=true"
        response = requests.get(url, timeout=10).json()
        temp = response['current_weather']['temperature']
        return f"🌡️ **Kraków:** {temp}°C"
    except: return "🌡️ **Hava Durumu:** Alınamadı"

def get_currency():
    try:
        url = "https://api.frankfurter.app/latest?from=TRY&to=EUR,PLN"
        data = requests.get(url, timeout=10).json()['rates']
        return f"💱 1 EUR = {round(1 / data['EUR'], 2)} TL | 1 PLN = {round(1 / data['PLN'], 2)} TL"
    except: return "💱 **Döviz:** Alınamadı"

def get_english_word():
    try:
        url = "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa-no-swears.txt"
        words = requests.get(url, timeout=10).text.split('\n')[500:3000]
        for _ in range(3):
            word = random.choice(words)
            res = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
            if res.status_code == 200:
                data = res.json()[0]
                definition = data['meanings'][0]['definitions'][0]['definition']
                return f"🧠 **{word.capitalize()}**: {definition}"
        return "🧠 Kelime alınamadı."
    except: return "🧠 Kelime alınamadı."

def get_quote():
    try:
        res = requests.get("https://zenquotes.io/api/random", timeout=10).json()
        return f"💡 _{res[0]['q']}_ — {res[0]['a']}"
    except: return "💡 Söz alınamadı."


# ==========================================
# 4. BUTONLARI OLUŞTURMA
# ==========================================
def bulten_butonlari():
    markup = InlineKeyboardMarkup()
    # Butonları ekliyoruz (callback_data kısmı botun hangi butona basıldığını anlaması içindir)
    btn1 = InlineKeyboardButton("💱 Kuru Güncelle", callback_data="btn_kur")
    btn2 = InlineKeyboardButton("🧠 Yeni Kelime Ver", callback_data="btn_kelime")
    btn3 = InlineKeyboardButton("💡 Başka Bir Söz", callback_data="btn_soz")
    
    markup.add(btn1) # Üst satır
    markup.add(btn2, btn3) # Alt satıra iki buton yan yana
    return markup


# ==========================================
# 5. BUTONLARA BASILINCA NE OLACAK? (ETKİLEŞİM)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def butona_basildi(call):
    # Telegram'da butona basınca üstte çıkan "Yükleniyor..." bildirimini kapatmak için
    bot.answer_callback_query(call.id)
    
    if call.data == "btn_kur":
        bot.send_message(call.message.chat.id, get_currency(), parse_mode="Markdown")
    elif call.data == "btn_kelime":
        bot.send_message(call.message.chat.id, get_english_word(), parse_mode="Markdown")
    elif call.data == "btn_soz":
        bot.send_message(call.message.chat.id, get_quote(), parse_mode="Markdown")


# ==========================================
# 6. HER SABAH 08:00'DE ÇALIŞACAK ZAMANLAYICI
# ==========================================
def sabah_bulteni_gonder():
    already_sent = False
    while True:
        current_hour = time.strftime("%H")
        if current_hour == "08" and not already_sent:
            bulten = (
                "☀️ **GÜNAYDIN!**\n\n"
                f"{get_weather()}\n\n"
                f"{get_currency()}\n\n"
                f"{get_english_word()}\n\n"
                f"{get_quote()}"
            )
            # Mesajı yollarken butonları da (reply_markup) ekliyoruz
            bot.send_message(CHAT_ID, bulten, parse_mode="Markdown", reply_markup=bulten_butonlari())
            already_sent = True
            
        if current_hour == "00":
            already_sent = False
            
        time.sleep(60)

# Zamanlayıcıyı ayrı bir işlem olarak başlatıyoruz (Botu kitlemesin diye)
Thread(target=sabah_bulteni_gonder, daemon=True).start()


# ==========================================
# 7. BOTU ÇALIŞTIR VE DİNLEMEYE BAŞLA
# ==========================================
print("Bot çalışıyor ve seni dinliyor...")
# Test etmek için ilk açılışta anında 1 tane mesaj göndersin:
test_mesaji = "Bot başarıyla başlatıldı. Butonları test edebilirsin!"
bot.send_message(CHAT_ID, test_mesaji, reply_markup=bulten_butonlari())

# Botun 7/24 mesaj ve buton tıklamalarını dinlemesini sağlar
bot.polling(none_stop=True)