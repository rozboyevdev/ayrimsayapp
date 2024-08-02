



import telebot
import json
import sqlite3
from telebot import types
from datetime import datetime

API_TOKEN = '7158602292:AAE9x3Lu-8iRdgi-o8CMfdbxFA649RN4Y5I'
ADMIN_CHAT_IDS = [1593464245]  # Admin chat ID'sini kiriting
ORDER_GROUP_ID = -4217845316  # Buyurtmalarni yuboradigan guruh ID'sini kiriting

bot = telebot.TeleBot(API_TOKEN)

# User data file
USER_DATA_FILE = 'users.json'

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()
user_states = {}

# Database connection
conn = sqlite3.connect('restaurant.db', check_same_thread=False)
cursor = conn.cursor()

# Ensure products table includes an image column
cursor.execute('''
CREATE TABLE IF NOT EXISTS products
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, net_price REAL, image TEXT)
''')
conn.commit()

# Ish vaqtini tekshirish uchun funksiya
def is_working_hours():
    now = datetime.now().time()
    start_time = datetime.strptime("09:00", "%H:%M").time()
    end_time = datetime.strptime("23:00", "%H:%M").time()
    return start_time <= now <= end_time

# Bosh menyu tugmalarini yaratish
def create_main_menu(language):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    menu_button = types.KeyboardButton("📜 Menyu" if language == "O'zbek" else "📜 Меню")
    contact_button = types.KeyboardButton("☎️ Kontakt" if language == "O'zbek" else "☎️ Контакт")
    order_button = types.KeyboardButton("🚖 Buyurtma" if language == "O'zbek" else "🚖 Заказ")
    cart_button = types.KeyboardButton("🛒 Savatcha" if language == "O'zbek" else "🛒 Корзина")
    settings_button = types.KeyboardButton("⚙️ Sozlamalar" if language == "O'zbek" else "⚙️ Настройки")
    markup.add(menu_button, contact_button, order_button, cart_button, settings_button)
    return markup

# Admin menyu tugmalarini yaratish
def create_admin_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    send_message_button = types.KeyboardButton("📢 Habar yuborish")
    add_button = types.KeyboardButton("🆕 Mahsulot qo'shish")
    edit_button = types.KeyboardButton("✏️ Mahsulot tahrirlash")
    delete_button = types.KeyboardButton("🗑️ Mahsulot o'chirish")
    back_button = types.KeyboardButton("⬅️ Orqaga")
    markup.add(send_message_button, add_button, edit_button, delete_button, back_button)
    return markup

# Bosh menyu
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if str(user_id) in user_data:
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
        user_data[message.chat.id] = {"language": language}
        save_user_data(user_data)
        msg = bot.reply_to(message, "Ismingizni kiriting:" if language == "O'zbek" else "Введите ваше имя:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_name_step, language)

def process_name_step(message, language):
    name = message.text
    if not name.isalpha():
        msg = bot.reply_to(message, "Iltimos, to'g'ri ismingizni kiriting:" if language == "O'zbek" else "Пожалуйста, введите правильное имя:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_name_step, language)
    else:
        user_data[message.chat.id]["name"] = name
        save_user_data(user_data)
        msg = bot.reply_to(message, "Telefon raqamingizni kiriting: +998XXXXXXXXX" if language == "O'zbek" else "Введите ваш номер телефона: +998XXXXXXXXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_phone_step, language)

def process_phone_step(message, language):
    phone = message.text
    if not phone.startswith("+998") or not phone[4:].isdigit() or len(phone) != 13:
        msg = bot.reply_to(message, "Iltimos, to'g'ri telefon raqamini kiriting: +998XXXXXXXXX" if language == "O'zbek" else "Пожалуйста, введите правильный номер телефона: +998XXXXXXXXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_phone_step, language)
    else:
        user_data[message.chat.id]["phone"] = phone
        save_user_data(user_data)
        msg = bot.reply_to(message, "Lakatsiyani jo'nating:" if language == "O'zbek" else "Отправьте ваше местоположение:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('Lakatsiyani yuboring' if language == "O'zbek" else 'Отправить местоположение', request_location=True)))
        bot.register_next_step_handler(msg, process_location_step, language)

def process_location_step(message, language):
    if not message.location:
        msg = bot.reply_to(message, "Iltimos, lokatsiyani jo'nating:" if language == "O'zbek" else "Пожалуйста, отправьте ваше местоположение:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('Lakatsiyani yuboring' if language == "O'zbek" else 'Отправить местоположение', request_location=True)))
        bot.register_next_step_handler(msg, process_location_step, language)
    else:
        location = f"{message.location.latitude},{message.location.longitude}"
        user_data[message.chat.id]["location"] = location
        save_user_data(user_data)
        bot.reply_to(message, "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!" if language == "O'zbek" else "Регистрация успешно завершена!", reply_markup=create_main_menu(language))
        send_main_menu(message)

def send_main_menu(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = create_main_menu(language)
    bot.send_message(message.chat.id, "Asosiy menyu:" if language == "O'zbek" else "Главное меню:", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def send_admin_menu(message):
    if message.chat.id in ADMIN_CHAT_IDS:
        markup = create_admin_menu()
        bot.reply_to(message, "Admin menyusi" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Админ меню", reply_markup=markup)
    else:
        bot.reply_to(message, "Siz admin emassiz." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Вы не администратор.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "📢 Habar yuborish" and message.chat.id in ADMIN_CHAT_IDS)
def send_message(message):
    msg = bot.reply_to(message, "Iltimos habarni kiriting:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите сообщение:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_send_message)

def process_send_message(message):
    for user_id in user_data.keys():
        try:
            bot.send_message(user_id, message.text)
        except:
            continue
    bot.reply_to(message, "Habar yuborildi." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Сообщение отправлено.", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "🆕 Mahsulot qo'shish" and message.chat.id in ADMIN_CHAT_IDS)
def add_product(message):
    msg = bot.reply_to(message, "Mahsulot nomini kiriting:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите название продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_name_step)

def process_product_name_step(message):
    product_name = message.text
    msg = bot.reply_to(message, "Mahsulotni sotuv narxini kiriting (xxx.xxx):" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите цену продукта (xxx.xxx):", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_price_step, product_name)

def process_product_price_step(message, product_name):
    try:
        product_price = float(message.text)
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri narx kiriting." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, введите правильную цену.", reply_markup=create_admin_menu())
        return
    msg = bot.reply_to(message, "Mahsulotni sof narxini kiriting (xxx.xxx) yoki /skip bosing:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите себестоимость продукта (xxx.xxx) или нажмите /skip:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_net_price_step, product_name, product_price)

def process_product_net_price_step(message, product_name, product_price):
    if message.text == '/skip':
        product_net_price = None
    else:
        try:
            product_net_price = float(message.text)
        except ValueError:
            bot.reply_to(message, "Iltimos, to'g'ri narx kiriting yoki /skip bosing." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, введите правильную цену или нажмите /skip.", reply_markup=create_admin_menu())
            return
    msg = bot.reply_to(message, "Mahsulot rasmini yuboring yoki /skip bosing:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Отправьте изображение продукта или нажмите /skip:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_image_step, product_name, product_price, product_net_price)

def process_product_image_step(message, product_name, product_price, product_net_price):
    if message.text == '/skip':
        product_image = None
    else:
        product_image = message.photo[-1].file_id
    cursor.execute("INSERT INTO products (name, price, net_price, image) VALUES (?, ?, ?, ?)",
                   (product_name, product_price, product_net_price, product_image))
    conn.commit()
    net_price_info = f" - {product_net_price} so'm" if product_net_price else ""
    bot.reply_to(message, f"Mahsulot qo'shildi: {product_name} - {product_price} so'm{net_price_info}" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Продукт добавлен: {product_name} - {product_price} сум{net_price_info}", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "✏️ Mahsulot tahrirlash" and message.chat.id in ADMIN_CHAT_IDS)
def edit_product(message):
    product_list = "\n".join([f"{row[0]}: {row[1]}" for row in cursor.execute("SELECT id, name FROM products")])
    if not product_list:
        bot.reply_to(message, "Hozircha mahsulotlar mavjud emas." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "На данный момент продуктов нет.", reply_markup=create_admin_menu())
        return
    msg = bot.reply_to(message, f"Mahsulotlar ro'yxati:\n{product_list}\nMahsulot IDsini kiriting:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Список продуктов:\n{product_list}\nВведите ID продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_edit_product_id_step)

def process_edit_product_id_step(message):
    try:
        product_id = int(message.text)
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            bot.reply_to(message, "Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Продукт не найден.", reply_markup=create_admin_menu())
            return
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri ID kiriting." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, введите правильный ID.", reply_markup=create_admin_menu())
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("Yangi nomni kiriting" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите новое название")
    edit_price_button = types.KeyboardButton("Yangi narxni kiriting" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите новую цену")
    back_button = types.KeyboardButton("⬅️ Orqaga" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "⬅️ Назад")
    markup.add(edit_name_button, edit_price_button, back_button)
    msg = bot.reply_to(message, "Tahrirlash variantini tanlang:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Выберите вариант редактирования:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_edit_option_step, product_id)

def process_edit_option_step(message, product_id):
    if message.text == ("Yangi nomni kiriting" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите новое название"):
        msg = bot.reply_to(message, "Yangi nomni kiriting:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите новое название:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_edit_product_name, product_id)
    elif message.text == ("Yangi narxni kiriting" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите новую цену"):
        msg = bot.reply_to(message, "Yangi narxni kiriting: XXX.XXX" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите новую цену: XXX.XXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_edit_product_price, product_id)
    elif message.text == ("⬅️ Orqaga" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "⬅️ Назад"):
        send_admin_menu(message)
    else:
        bot.reply_to(message, "Iltimos, tahrirlash variantini tanlang." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, выберите вариант редактирования.", reply_markup=create_admin_menu())

def process_edit_product_name(message, product_id):
    new_name = message.text
    cursor.execute("UPDATE products SET name = ? WHERE id = ?", (new_name, product_id))
    conn.commit()
    bot.reply_to(message, f"Mahsulot nomi yangilandi: {new_name}" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Название продукта обновлено: {new_name}", reply_markup=create_admin_menu())

def process_edit_product_price(message, product_id):
    try:
        new_price = float(message.text)
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri narx kiriting." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, введите правильную цену.", reply_markup=create_admin_menu())
        return
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()
    bot.reply_to(message, f"Mahsulot narxi yangilandi: {new_price} so'm" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Цена продукта обновлена: {new_price} сум", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "🗑️ Mahsulot o'chirish" and message.chat.id in ADMIN_CHAT_IDS)
def delete_product(message):
    product_list = "\n".join([f"{row[0]}: {row[1]}" for row in cursor.execute("SELECT id, name FROM products")])
    if not product_list:
        bot.reply_to(message, "Hozircha mahsulotlar mavjud emas." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "На данный момент продуктов нет.", reply_markup=create_admin_menu())
        return
    msg = bot.reply_to(message, f"Mahsulotlar ro'yxati:\n{product_list}\nMahsulot IDsini kiriting:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Список продуктов:\n{product_list}\nВведите ID продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_delete_product_id_step)

def process_delete_product_id_step(message):
    try:
        product_id = int(message.text)
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        bot.reply_to(message, f"Mahsulot o'chirildi: ID {product_id}" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Продукт удален: ID {product_id}", reply_markup=create_admin_menu())
    except ValueError:
        bot.reply_to(message, "Iltimos, to'g'ri ID kiriting." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, введите правильный ID.", reply_markup=create_admin_menu())

@bot.message_handler(func=lambda message: message.text == "📜 Menyu" or message.text == "📜 Меню")
def show_menu(message):
    language = user_data[str(message.chat.id)]["language"]
    cursor.execute("SELECT DISTINCT name FROM products")
    products_list = cursor.fetchall()
    if not products_list:
        bot.reply_to(message, "Hozircha menyuda hech narsa yuq." if language == "O'zbek" else "В меню пока ничего нет.", reply_markup=create_main_menu(language))
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    back_button = types.KeyboardButton("⬅️ Orqaga" if language == "O'zbek" else "⬅️ Назад")
    for product in products_list:
        markup.add(types.KeyboardButton(product[0]))
    markup.add(back_button)
    msg = bot.reply_to(message, "Mahsulotni tanlang:" if language == "O'zbek" else "Выберите продукт:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_product_details)

def show_product_details(message):
    if message.text == "⬅️ Orqaga" or message.text == "⬅️ Назад":
        send_main_menu(message)
        return

    product_name = message.text
    cursor.execute("SELECT * FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()
    if not product:
        bot.reply_to(message, "Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Продукт не найден.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    user_states[message.chat.id] = {'product_id': product[0], 'quantity': 1}
    language = user_data[str(message.chat.id)]["language"]
    caption = f"{product[1]}\n\n{product[2]} so'm" if language == "O'zbek" else f"{product[1]}\n\n{product[2]} сум"
    if product[3]:
        caption += f" - {product[3]} so'm" if language == "O'zbek" else f" - {product[3]} сум"
    
    if product[4]:
        bot.send_photo(message.chat.id, product[4], caption=caption)
    else:
        bot.send_message(message.chat.id, caption)
    
    update_quantity_message(message)

def update_quantity_message(message):
    state = user_states[message.chat.id]
    language = user_data[str(message.chat.id)]["language"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="-", callback_data="decrease"),
               types.InlineKeyboardButton(text=str(state['quantity']), callback_data="quantity"),
               types.InlineKeyboardButton(text="+", callback_data="increase"))
    markup.add(types.InlineKeyboardButton(text="Qo'shish" if language == "O'zbek" else "Добавить", callback_data="add_to_cart"),
               types.InlineKeyboardButton(text="Bekor qilish" if language == "O'zbek" else "Отмена", callback_data="cancel"))
    bot.send_message(message.chat.id, f"Nechta buyurtma qilasiz?" if language == "O'zbek" else f"Сколько хотите заказать?", reply_markup=markup)

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
                              text=f"Savatingizga qo'shildi: {state['quantity']} dona" if user_data[str(call.message.chat.id)]["language"] == "O'zbek" else f"Добавлено в корзину: {state['quantity']} шт")
    elif call.data == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Bekor qilindi" if user_data[str(call.message.chat.id)]["language"] == "O'zbek" else "Отменено")

@bot.message_handler(func=lambda message: message.text == "☎️ Kontakt" or message.text == "☎️ Контакт")
def show_contact(message):
    bot.reply_to(message, "Murijaat uchun: +998 99 640 33 37\n@roziboyevdev" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Контакты: +998 99 640 33 37\n@roziboyevdev", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "🚖 Buyurtma" or message.text == "🚖 Заказ")
def place_order(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    if not is_working_hours():
        bot.reply_to(message, "Ish vaqti 09:00dan 23:00gacha" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Рабочее время с 09:00 до 23:00", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    msg = bot.reply_to(message, "Telefon raqamingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Введите ваш номер телефона:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, get_phone_number)

def get_phone_number(message):
    phone_number = message.text
    msg = bot.reply_to(message, "Lokatsiyangizni jo'nating:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Отправьте ваше местоположение:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('Lakatsiyani yuboring' if user_data[str(message.chat.id)]["language"] == "O'zbek" else 'Отправить местоположение', request_location=True)))
    bot.register_next_step_handler(msg, get_location, phone_number)

def get_location(message, phone_number):
    if not message.location:
        bot.reply_to(message, "Iltimos, lokatsiyani jo'nating." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, отправьте ваше местоположение.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    location = f"{message.location.latitude},{message.location.longitude}"
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()

    order_message = "Yangi buyurtma:\n" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Новый заказ:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        order_message += f"{item[0]} : {item[1]} x {item[2]} so'm = {item_price} so'm\n" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"{item[0]} : {item[1]} x {item[2]} сум = {item_price} сум\n"
        total_price += item_price
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, phone, location) VALUES (?, ?, ?, ?, ?)", (user_id, item[1], item[2], phone_number, location))
    order_message += f"Jami: {total_price} so'm\nTelefon: {phone_number}\nLokatsiya: {location}" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Итого: {total_price} сум\nТелефон: {phone_number}\nМестоположение: {location}"
    conn.commit()
    bot.send_message(ORDER_GROUP_ID, order_message)
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz siz bilan bog'lanadi!" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Ваш заказ принят! Операторы свяжутся с вами в ближайшее время!", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "🛒 Savatcha" or message.text == "🛒 Корзина")
def show_cart(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    cart_message = "Sizning savatingiz:\n" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Ваша корзина:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        cart_message += f"{item[0]} : {item[1]} x {item[2]} so'm = {item_price} so'm\n" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"{item[0]} : {item[1]} x {item[2]} сум = {item_price} сум\n"
        total_price += item_price
    cart_message += f"Jami: {total_price} so'm" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Итого: {total_price} сум"

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    order_history_button = types.KeyboardButton("Buyurtmalar tarixi" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "История заказов")
    remove_product_button = types.KeyboardButton("Mahsulotni olib tashlash" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Удалить продукт")
    clear_cart_button = types.KeyboardButton("Savatchani tozalash" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Очистить корзину")
    place_order_button = types.KeyboardButton("Buyurtma qilish" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Сделать заказ")
    back_button = types.KeyboardButton("⬅️ Orqaga" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "⬅️ Назад")
    markup.add(order_history_button, remove_product_button, clear_cart_button, place_order_button, back_button)

    bot.send_message(message.chat.id, cart_message, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Buyurtmalar tarixi" or message.text == "История заказов")
def show_order_history(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, orders.quantity, orders.price FROM orders JOIN products ON orders.product_id = products.id WHERE orders.user_id = ?", (user_id,))
    orders = cursor.fetchall()
    if not orders:
        bot.reply_to(message, "Buyurtmalar tarixi mavjud emas." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "История заказов отсутствует.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    history_message = "Sizning buyurtmalar tarixi:\n" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Ваша история заказов:\n"
    for order in orders:
        order_total = order[1] * order[2]
        history_message += f"{order[0]} : {order[1]} x {order[2]} so'm = {order_total} so'm\n" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"{order[0]} : {order[1]} x {order[2]} сум = {order_total} сум\n"
    bot.send_message(message.chat.id, history_message, reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "Mahsulotni olib tashlash" or message.text == "Удалить продукт")
def remove_product(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.id, products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "Savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in cart_items:
        markup.add(types.KeyboardButton(f"{item[1]} - {item[2]} x {item[3]}"))
    markup.add(types.KeyboardButton("⬅️ Orqaga" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "⬅️ Назад"))
    msg = bot.reply_to(message, "Olib tashlanadigan mahsulotni tanlang:" if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Выберите продукт для удаления:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_remove_product)

def process_remove_product(message):
    if message.text == "⬅️ Orqaga" or message.text == "⬅️ Назад":
        show_cart(message)
        return

    product_info = message.text.split(" - ")[0]
    user_id = message.from_user.id
    cursor.execute("SELECT id FROM products WHERE name = ?", (product_info,))
    product_id = cursor.fetchone()
    if product_id:
        cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id[0]))
        conn.commit()
        bot.reply_to(message, "Mahsulot savatchadan olib tashlandi." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Продукт удален из корзины.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
    else:
        bot.reply_to(message, "Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Продукт не найден.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "Savatchani tozalash" or message.text == "Очистить корзину")
def clear_cart(message):
    user_id = message.from_user.id
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "Savatcha tozalandi." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Корзина очищена.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "Buyurtma qilish" or message.text == "Сделать заказ")
def confirm_order(message):
    place_order(message)

@bot.message_handler(func=lambda message: message.text == "⚙️ Sozlamalar" or message.text == "⚙️ Настройки")
def show_settings(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("Ismni o'zgartirish" if language == "O'zbek" else "Изменить имя")
    change_language_button = types.KeyboardButton("Tilni o'zgartirish" if language == "O'zbek" else "Изменить язык")
    back_button = types.KeyboardButton("⬅️ Orqaga" if language == "O'zbek" else "⬅️ Назад")
    markup.add(edit_name_button, change_language_button, back_button)
    msg = bot.reply_to(message, "Sozlamalar:" if language == "O'zbek" else "Настройки:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_settings)

def process_settings(message):
    language = user_data[str(message.chat.id)]["language"]
    if message.text == "Ismni o'zgartirish" or message.text == "Изменить имя":
        msg = bot.reply_to(message, "Yangi ismingizni kiriting:" if language == "O'zbek" else "Введите ваше новое имя:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, change_name)
    elif message.text == "Tilni o'zgartirish" or message.text == "Изменить язык":
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        uzb_button = types.KeyboardButton("O'zbek")
        rus_button = types.KeyboardButton("русский")
        markup.add(uzb_button, rus_button)
        msg = bot.reply_to(message, "Tilni tanlang:" if language == "O'zbek" else "Выберите язык:", reply_markup=markup)
        bot.register_next_step_handler(msg, change_language)
    elif message.text == "⬅️ Orqaga" or message.text == "⬅️ Назад":
        send_main_menu(message)

def change_name(message):
    new_name = message.text
    user_id = message.from_user.id
    user_data[str(user_id)]["name"] = new_name
    save_user_data(user_data)
    bot.reply_to(message, f"Ismingiz o'zgartirildi: {new_name}" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Ваше имя изменено: {new_name}", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

def change_language(message):
    new_language = message.text
    if new_language not in ["O'zbek", "русский"]:
        bot.reply_to(message, "Iltimos, tilni tanlang." if user_data[str(message.chat.id)]["language"] == "O'zbek" else "Пожалуйста, выберите язык.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return
    user_id = message.from_user.id
    user_data[str(user_id)]["language"] = new_language
    save_user_data(user_data)
    bot.reply_to(message, f"Til o'zgartirildi: {new_language}" if user_data[str(message.chat.id)]["language"] == "O'zbek" else f"Язык изменен: {new_language}", reply_markup=create_main_menu(new_language))

# Botni ishga tushiramiz
bot.infinity_polling()


