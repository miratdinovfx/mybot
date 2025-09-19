import telebot
from telebot import types
import sqlite3

API_TOKEN = "8041913948:AAF4B6imGN0_76qbFDExeMihgrhk-9Vq4vQ"
TELEGRAM_CHANNEL = "@Karauzak_school"
INSTAGRAM_LINK = "https://instagram.com/karauzak_school"
ADMIN_ID = 615739450  # faqat shu ID admin

bot = telebot.TeleBot(API_TOKEN)
DB_FILE = "bot_data.db"

# ----------------- Database funksiyalari -----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            score INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_or_update_user(user_id, full_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users(user_id, full_name) VALUES(?, ?)", (user_id, full_name))
    cursor.execute("UPDATE users SET full_name=? WHERE user_id=?", (full_name, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name, score FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def add_score(user_id, points):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET score = score + ? WHERE user_id=?", (points, user_id))
    conn.commit()
    cursor.execute("SELECT full_name, score FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# 🔴 0 ballga ega bo‘lganlarni olish emas, faqat score>0
def get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT full_name, score 
        FROM users 
        WHERE score > 0 
        ORDER BY score DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def reset_all_scores():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET score = 0")
    conn.commit()
    conn.close()

# ----------------- Bot funksiyalari -----------------
@bot.message_handler(commands=['start'])
def start(message):
    user = get_user(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user:
        markup.row("👤 Juwap jiberiw", "👤 Profilim")
        markup.row("📊 Statistika")
        bot.send_message(message.chat.id, f"Sálem, {user[0]}! Menyu arqalı dawam etiwińiz múmkin ✅", reply_markup=markup)
        return

    markup_inline = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("📩 Telegram kanal", url=f"https://t.me/{TELEGRAM_CHANNEL.strip('@')}")
    btn2 = types.InlineKeyboardButton("📷 Instagram sahifa", url=INSTAGRAM_LINK)
    btn3 = types.InlineKeyboardButton("✅ Tekseriw", callback_data="check_subscription")
    markup_inline.row(btn1, btn2)
    markup_inline.add(btn3)
    bot.send_message(message.chat.id,
                     "Sálem!Sorawlarda qatnasıw ushın tómendegi kanallarģa aģza bolıń,soń ✅️ Tekseriw túymesin basıń.",
                     reply_markup=markup_inline)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    try:
        bot.answer_callback_query(call.id)
        status = bot.get_chat_member(TELEGRAM_CHANNEL, call.from_user.id)
        if status.status in ["member", "administrator", "creator"]:
            bot.send_message(call.from_user.id,
                             "✅ Jazılıw qabıllandı! Iltimas, atıńız hám familiyańızdı jazıp jiberiń.")
            bot.register_next_step_handler_by_chat_id(call.from_user.id, get_name)
        else:
            bot.send_message(call.from_user.id, "❌ Siz ele Telegram kanalģa aģza bolmaģansız!")
    except Exception as e:
        bot.send_message(call.from_user.id, f"Qátelik: {e}")

def get_name(message):
    if not message.text:
        bot.send_message(message.chat.id, "Iltimas, tekst kórinisinde atıńız hám familiyańızdı jiberiń")
        bot.register_next_step_handler(message, get_name)
        return
    full_name = message.text.strip()
    add_or_update_user(message.from_user.id, full_name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("👤 Juwap jiberiw", "👤 Profilim")
    markup.row("📊 Statistika")
    bot.send_message(message.chat.id, f"Raxmet, {full_name}! Endi menyudan paydalanıwıńız múmkin ✅", reply_markup=markup)

@bot.message_handler(commands=['reset'])
def reset_scores(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Bu buyruqni faqat admin ishlata oladi.")
        return
    reset_all_scores()
    bot.reply_to(message, "✅ Barcha foydalanuvchilar ballari 0 ga tushirildi.")

@bot.message_handler(func=lambda msg: msg.text)
def main_menu(message):
    user = get_user(message.from_user.id)
    if not user:
        bot.send_message(message.chat.id, "Iltimas, aldın atıńızdı jiberiń.")
        bot.register_next_step_handler_by_chat_id(message.from_user.id, get_name)
        return
    text = message.text
    if text == "👤 Profilim":
        bot.send_message(message.chat.id, f"👤 Atıńız: {user[0]}\n⭐ Ballar: {user[1]}")
    elif text == "📊 Statistika":
        leaderboard = get_leaderboard()
        if leaderboard:
            text = "🏆 Top paydalanıwshılar:\n\n"
            for i, (name, score) in enumerate(leaderboard, 1):
                text += f"{i}. {name} — {score} ball\n"
            bot.send_message(message.chat.id, text)
        else:
            bot.send_message(message.chat.id, "Házirshe balli paydalanıwshılar joq.")
    elif text == "👤 Juwap jiberiw":
        bot.send_message(message.chat.id, "Sorawģa juwabıńızdı jiberiń:")
        bot.register_next_step_handler(message, receive_answer)

def receive_answer(message):
    uid = message.from_user.id
    user = get_user(uid)
    full_name = user[0]
    answer = message.text if message.text else "<Matn bo'lmagan kontent>"
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.row(
        types.InlineKeyboardButton("✅ Durıs", callback_data=f"check_{uid}_1"),
        types.InlineKeyboardButton("❌ Nadurıs", callback_data=f"check_{uid}_0")
    )
    admin_msg = f"👆 Jańa juwap!!\nIsm: {full_name}\nUser ID: {uid}\nJuwap:\n{answer}"
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=admin_markup)
    bot.send_message(message.chat.id, f"✅ Juwabıńız qabıllandı, {full_name}! Admin tekseredi")

@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("check_"))
def handle_check(c):
    parts = c.data.split("_")
    target_id = int(parts[1])
    points = int(parts[2])
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ Bul ámeliyattı tek admin isley aladı.", show_alert=True)
        return
    full_name, new_score = add_score(target_id, points)
    status_text = "✅ Durıs" if points == 1 else "❌ Nadurıs"
    updated_text = f"{c.message.text}\n\n➡ Admin tekseredi: {status_text}"
    bot.edit_message_text(chat_id=c.message.chat.id, message_id=c.message.message_id, text=updated_text)
    bot.answer_callback_query(c.id, f"✅ Juwap tekserildi. Jańa ball.: {new_score}")
    msg = "🎉 Juwabıńız durıs! Sizge 1 ball qosıldı." if points == 1 else "❌ Juwabıńız nadurıs. Sizge ball qosılmadı."
    try:
        bot.send_message(target_id, msg)
    except Exception:
        pass

# ----------------- Ishga tushirish -----------------
if __name__ == "__main__":
    init_db()
    print("Bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)
