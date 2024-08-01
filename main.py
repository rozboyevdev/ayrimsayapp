import telebot
import sqlite3
from telebot import types
from datetime import datetime

API_TOKEN = '7158602292:AAE9x3Lu-8iRdgi-o8CMfdbxFA649RN4Y5I'
ADMIN_CHAT_IDS = [1593464245]  # Admin chat ID'sini kiriting
ORDER_GROUP_ID = -4217845316  # Buyurtmalarni yuboradigan guruh ID'sini kiriting

bot = telebot.TeleBot(API_TOKEN)

# Ma'lumotlar bazasini sozlash
conn = sqlite3.connect('restaurant.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS products
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, net_price REAL)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS cart
             (user_id INTEGER, product_id INTEGER, quantity INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS orders
             (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, quantity INTEGER, phone TEXT, location TEXT, order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, name TEXT, phone TEXT, location TEXT, language TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS admins
             (user_id INTEGER PRIMARY KEY)''')
conn.commit()

user_states = {}

# Ish vaqtini tekshirish uchun funksiya
def is_working_hours():
    now = datetime.now().time()
    start_time = datetime.strptime("09:00", "%H:%M").time()
    end_time = datetime.strptime("23:00", "%H:%M").time()
    return start_time <= now >= end_time

# Bosh menyu tugmalarini yaratish
def create_main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    menu_button = types.KeyboardButton("📜 Menyu")
    contact_button = types.KeyboardButton("☎️ Kontakt")
    order_button = types.KeyboardButton("🚖 Buyurtma")
    cart_button = types.KeyboardButton("🛒 Savatcha")
    settings_button = types.KeyboardButton("⚙️ Sozlamalar")
    markup.add(menu_button, contact_button, order_button, cart_button, settings_button)
    return markup

# Admin menyu tugmalarini yaratish
def create_admin_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    send_message_button = types.KeyboardButton("📢 Habar yuborish")
    add_button = types.KeyboardButton("🆕 Mahsulot qo'shish")
    edit_button = types.KeyboardButton("✏️ Mahsulot tahrirlash")
    delete_button = types.KeyboardButton("🗑️ Mahsulot o'chirish")
    add_admin_button = types.KeyboardButton("➕ Admin qo'shish")
    remove_admin_button = types.KeyboardButton("➖ Admin o'chirish")
    back_button = types.KeyboardButton("⬅️ Orqaga")
    markup.add(send_message_button, add_button, edit_button, delete_button, add_admin_button, remove_admin_button, back_button)
    return markup

# Bosh menyu
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        send_main_menu(message)
    else:
        start_registration(message)

def start_registration(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    uzb_button = types.KeyboardButton("O'zbek")
    rus_button = types.KeyboardButton("русский")
    markup.add(uzb_button, rus_button)
    msg = bot.reply_to(message, "Tilni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_language_step)

def process_language_step(message):
    language = message.text
    if language not in ["O'zbek", "русский"]:
        msg = bot.reply_to(message, "Iltimos, tilni tanlang:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton("O'zbek"), types.KeyboardButton("русский")))
        bot.register_next_step_handler(msg, process_language_step)
    else:
        msg = bot.reply_to(message, "Ismingizni kiriting:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_name_step, language)

def process_name_step(message, language):
    name = message.text
    if not name.isalpha():
        msg = bot.reply_to(message, "Iltimos, to'g'ri ismingizni kiriting:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_name_step, language)
    else:
        msg = bot.reply_to(message, "Telefon raqamingizni kiriting: +998XXXXXXXXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_phone_step, language, name)

def process_phone_step(message, language, name):
    phone = message.text
    if not phone.startswith("+998") or not phone[4:].isdigit() or len(phone) != 13:
        msg = bot.reply_to(message, "Iltimos, to'g'ri telefon raqamini kiriting: +998XXXXXXXXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_phone_step, language, name)
    else:
        msg = bot.reply_to(message, "Lakatsiyani jo'nating:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('Lakatsiyani yuboring', request_location=True)))
        bot.register_next_step_handler(msg, process_location_step, language, name, phone)

def process_location_step(message, language, name, phone):
    if not message.location:
        msg = bot.reply_to(message, "Iltimos, lokatsiyani jo'nating:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('Lakatsiyani yuboring', request_location=True)))
        bot.register_next_step_handler(msg, process_location_step, language, name, phone)
    else:
        location = f"{message.location.latitude},{message.location.longitude}"
        user_id = message.chat.id

        cursor.execute("INSERT INTO users (user_id, name, phone, location, language) VALUES (?, ?, ?, ?, ?)", 
                       (user_id, name, phone, location, language))
        conn.commit()
        bot.reply_to(message, "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!", reply_markup=create_main_menu())
        send_main_menu(message)

def send_main_menu(message):
    markup = create_main_menu()
    bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def send_admin_menu(message):
    if message.chat.id in ADMIN_CHAT_IDS:
        markup = create_admin_menu()
        bot.reply_to(message, "Admin menyusi", reply_markup=markup)
    else:
        bot.reply_to(message, "Siz admin emassiz.", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "📢 Habar yuborish" and message.chat.id in ADMIN_CHAT_IDS)
def send_message(message):
    msg = bot.reply_to(message, "Iltimos habarni kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_send_message)

def process_send_message(message):
    for user_id in [row[0] for row in cursor.execute("SELECT user_id FROM users")]:
        try:
            bot.send_message(user_id, message.text)
        except:
            continue
    bot.reply_to(message, "Habar yuborildi.", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "🆕 Mahsulot qo'shish" and message.chat.id in ADMIN_CHAT_IDS)
def add_product(message):
    msg = bot.reply_to(message, "Mahsulot nomini kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_name_step)

def process_product_name_step(message):
    product_name = message.text
    msg = bot.reply_to(message, "Mahsulotni sotuv narxini kiriting (xxx.xxx):", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_price_step, product_name)

def process_product_price_step(message, product_name):
    try:
        product_price = float(message.text)
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri narx kiriting.", reply_markup=create_admin_menu())
        return
    msg = bot.reply_to(message, "Mahsulotni sof narxini kiriting (xxx.xxx) yoki /skip bosing:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_net_price_step, product_name, product_price)

def process_product_net_price_step(message, product_name, product_price):
    if message.text == '/skip':
        product_net_price = None
    else:
        try:
            product_net_price = float(message.text)
        except ValueError:
            bot.reply_to(message, "Iltimos, to'g'ri narx kiriting yoki /skip bosing.", reply_markup=create_admin_menu())
            return
    cursor.execute("INSERT INTO products (name, price, net_price) VALUES (?, ?, ?)",
                   (product_name, product_price, product_net_price))
    conn.commit()
    net_price_info = f" - {product_net_price} so'm" if product_net_price else ""
    bot.reply_to(message, f"Mahsulot qo'shildi: {product_name} - {product_price} so'm{net_price_info}", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "✏️ Mahsulot tahrirlash" and message.chat.id in ADMIN_CHAT_IDS)
def edit_product(message):
    product_list = "\n".join([f"{row[0]}: {row[1]}" for row in cursor.execute("SELECT id, name FROM products")])
    if not product_list:
        bot.reply_to(message, "Hozircha mahsulotlar mavjud emas.", reply_markup=create_admin_menu())
        return
    msg = bot.reply_to(message, f"Mahsulotlar ro'yxati:\n{product_list}\nMahsulot IDsini kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_edit_product_id_step)

def process_edit_product_id_step(message):
    try:
        product_id = int(message.text)
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            bot.reply_to(message, "Bunday mahsulot topilmadi.", reply_markup=create_admin_menu())
            return
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri ID kiriting.", reply_markup=create_admin_menu())
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("Yangi nomni kiriting")
    edit_price_button = types.KeyboardButton("Yangi narxni kiriting")
    back_button = types.KeyboardButton("⬅️ Orqaga")
    markup.add(edit_name_button, edit_price_button, back_button)
    msg = bot.reply_to(message, "Tahrirlash variantini tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_edit_option_step, product_id)

def process_edit_option_step(message, product_id):
    if message.text == "Yangi nomni kiriting":
        msg = bot.reply_to(message, "Yangi nomni kiriting:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_edit_product_name, product_id)
    elif message.text == "Yangi narxni kiriting":
        msg = bot.reply_to(message, "Yangi narxni kiriting: XXX.XXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_edit_product_price, product_id)
    elif message.text == "⬅️ Orqaga":
        send_admin_menu(message)
    else:
        bot.reply_to(message, "Iltimos, tahrirlash variantini tanlang.", reply_markup=create_admin_menu())

def process_edit_product_name(message, product_id):
    new_name = message.text
    cursor.execute("UPDATE products SET name = ? WHERE id = ?", (new_name, product_id))
    conn.commit()
    bot.reply_to(message, f"Mahsulot nomi yangilandi: {new_name}", reply_markup=create_admin_menu())

def process_edit_product_price(message, product_id):
    try:
        new_price = float(message.text)
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri narx kiriting.", reply_markup=create_admin_menu())
        return
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()
    bot.reply_to(message, f"Mahsulot narxi yangilandi: {new_price} so'm", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "🗑️ Mahsulot o'chirish" and message.chat.id in ADMIN_CHAT_IDS)
def delete_product(message):
    product_list = "\n".join([f"{row[0]}: {row[1]}" for row in cursor.execute("SELECT id, name FROM products")])
    if not product_list:
        bot.reply_to(message, "Hozircha mahsulotlar mavjud emas.", reply_markup=create_admin_menu())
        return
    msg = bot.reply_to(message, f"Mahsulotlar ro'yxati:\n{product_list}\nMahsulot IDsini kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_delete_product_id_step)

def process_delete_product_id_step(message):
    try:
        product_id = int(message.text)
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        bot.reply_to(message, f"Mahsulot o'chirildi: ID {product_id}", reply_markup=create_admin_menu())
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri ID kiriting.", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "➕ Admin qo'shish" and message.chat.id in ADMIN_CHAT_IDS)
def add_admin(message):
    msg = bot.reply_to(message, "Qo'shmoqchi bo'lgan adminning ID'sini kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_add_admin)

def process_add_admin(message):
    try:
        new_admin_id = int(message.text)
        cursor.execute("INSERT INTO admins (user_id) VALUES (?)", (new_admin_id,))
        conn.commit()
        ADMIN_CHAT_IDS.append(new_admin_id)
        bot.reply_to(message, f"Admin qo'shildi: {new_admin_id}", reply_markup=create_admin_menu())
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri ID kiriting.", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "➖ Admin o'chirish" and message.chat.id in ADMIN_CHAT_IDS)
def remove_admin(message):
    msg = bot.reply_to(message, "O'chirmoqchi bo'lgan adminning ID'sini kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_remove_admin)

def process_remove_admin(message):
    try:
        remove_admin_id = int(message.text)
        cursor.execute("DELETE FROM admins WHERE user_id = ?", (remove_admin_id,))
        conn.commit()
        ADMIN_CHAT_IDS.remove(remove_admin_id)
        bot.reply_to(message, f"Admin o'chirildi: {remove_admin_id}", reply_markup=create_admin_menu())
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri ID kiriting.", reply_markup=create_admin_menu())

# Bosh menyu
@bot.message_handler(func=lambda message: message.text == "📜 Menyu")
def show_menu(message):
    cursor.execute("SELECT DISTINCT name FROM products")
    products_list = cursor.fetchall()
    if not products_list:
        bot.reply_to(message, "Hozircha menyuda hech narsa yuq.", reply_markup=create_main_menu())
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    back_button = types.KeyboardButton("⬅️ Orqaga")
    for product in products_list:
        markup.add(types.KeyboardButton(product[0]))
    markup.add(back_button)
    msg = bot.reply_to(message, "Mahsulotni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_product_details)

def show_product_details(message):
    if message.text == "⬅️ Orqaga":
        send_main_menu(message)
        return

    product_name = message.text
    cursor.execute("SELECT * FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()
    if not product:
        bot.reply_to(message, "Bunday mahsulot topilmadi.", reply_markup=create_main_menu())
        return

    user_states[message.chat.id] = {'product_id': product[0], 'quantity': 1}
    update_quantity_message(message)

def update_quantity_message(message):
    state = user_states[message.chat.id]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="-", callback_data="decrease"),
               types.InlineKeyboardButton(text=str(state['quantity']), callback_data="quantity"),
               types.InlineKeyboardButton(text="+", callback_data="increase"))
    markup.add(types.InlineKeyboardButton(text="Qo'shish", callback_data="add_to_cart"),
               types.InlineKeyboardButton(text="Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, f"Nechta {state['product_id']} buyurtma qilasiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["decrease", "increase", "add_to_cart", "cancel"])
def callback_inline(call):
    state = user_states[call.message.chat.id]
    if call.data == "decrease":
        if state['quantity'] > 1:
            state['quantity'] -= 1
        update_quantity_message(call.message)
    elif call.data == "increase":
        state['quantity'] += 1
        update_quantity_message(call.message)
    elif call.data == "add_to_cart":
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)", 
                       (call.message.chat.id, state['product_id'], state['quantity']))
        conn.commit()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"Savatingizga qo'shildi: {state['quantity']} dona")
    elif call.data == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Bekor qilindi")

@bot.message_handler(func=lambda message: message.text == "☎️ Kontakt")
def show_contact(message):
    bot.reply_to(message, "Murijaat uchun: +998 99 640 33 37\n@roziboyevdev", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "🚖 Buyurtma")
def place_order(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "Sizning savatingiz bo'sh.", reply_markup=create_main_menu())
        return

    if not is_working_hours():
        bot.reply_to(message, "Ish vaqti 09:00dan 23:00gacha", reply_markup=create_main_menu())
        return

    msg = bot.reply_to(message, "Telefon raqamingizni kiriting:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, get_phone_number)

def get_phone_number(message):
    phone_number = message.text
    msg = bot.reply_to(message, "Lokatsiyangizni jo'nating:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('Lakatsiyani yuboring', request_location=True)))
    bot.register_next_step_handler(msg, get_location, phone_number)

def get_location(message, phone_number):
    if not message.location:
        bot.reply_to(message, "Iltimos, lokatsiyani jo'nating.", reply_markup=create_main_menu())
        return

    location = f"{message.location.latitude},{message.location.longitude}"
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()

    order_message = "Yangi buyurtma:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        order_message += f"{item[0]} : {item[1]} x {item[2]} so'm = {item_price} so'm\n"
        total_price += item_price
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, phone, location) VALUES (?, ?, ?, ?, ?)", (user_id, item[1], item[2], phone_number, location))
    order_message += f"Jami: {total_price} so'm\nTelefon: {phone_number}\nLokatsiya: {location}"
    conn.commit()
    bot.send_message(ORDER_GROUP_ID, order_message)
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz siz bilan bog'lanadi!", reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "🛒 Savatcha")
def show_cart(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "Sizning savatingiz bo'sh.", reply_markup=create_main_menu())
        return

    cart_message = "Sizning savatingiz:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        cart_message += f"{item[0]} : {item[1]} x {item[2]} so'm = {item_price} so'm\n"
        total_price += item_price
    cart_message += f"Jami: {total_price} so'm"
    bot.send_message(message.chat.id, cart_message, reply_markup=create_main_menu())

@bot.message_handler(func=lambda message: message.text == "⚙️ Sozlamalar")
def show_settings(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("Ismni o'zgartirish")
    change_language_button = types.KeyboardButton("Tilni o'zgartirish")
    back_button = types.KeyboardButton("⬅️ Orqaga")
    markup.add(edit_name_button, change_language_button, back_button)
    msg = bot.reply_to(message, "Sozlamalar:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_settings)

def process_settings(message):
    if message.text == "Ismni o'zgartirish":
        msg = bot.reply_to(message, "Yangi ismingizni kiriting:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, change_name)
    elif message.text == "Tilni o'zgartirish":
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        uzb_button = types.KeyboardButton("O'zbek")
        rus_button = types.KeyboardButton("русский")
        markup.add(uzb_button, rus_button)
        msg = bot.reply_to(message, "Tilni tanlang:", reply_markup=markup)
        bot.register_next_step_handler(msg, change_language)
    elif message.text == "⬅️ Orqaga":
        send_main_menu(message)

def change_name(message):
    new_name = message.text
    user_id = message.from_user.id
    cursor.execute("UPDATE users SET name = ? WHERE user_id = ?", (new_name, user_id))
    conn.commit()
    bot.reply_to(message, f"Ismingiz o'zgartirildi: {new_name}", reply_markup=create_main_menu())

def change_language(message):
    new_language = message.text
    if new_language not in ["O'zbek", "русский"]:
        bot.reply_to(message, "Iltimos, tilni tanlang.", reply_markup=create_main_menu())
        return
    user_id = message.from_user.id
    cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (new_language, user_id))
    conn.commit()
    bot.reply_to(message, f"Til o'zgartirildi: {new_language}", reply_markup=create_main_menu())

# Botni ishga tushiramiz
bot.infinity_polling()
