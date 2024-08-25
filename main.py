
import telebot
import json
import sqlite3
from telebot import types
from datetime import datetime

API_TOKEN = "7158602292:AAE9x3Lu-8iRdgi-o8CMfdbxFA649RN4Y5I"
ADMIN_CHAT_IDS = [1593464245,731577459,2052143248,6345168287,787534598]  # Admin chat ID'sini kiriting
ORDER_GROUP_ID = -1002165519452  # Buyurtmalarni yuboradigan guruh ID'sini kiriting

bot = telebot.TeleBot(API_TOKEN)

USER_DATA_FILE = 'users.json'

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as f:
            data = f.read()
            if data.strip():
                return json.loads(data)
            else:
                return {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()
user_states = {}

conn = sqlite3.connect('restaurant.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS products
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price TEXT, net_price TEXT, image TEXT, category TEXT)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS cart
(user_id INTEGER, product_id INTEGER, quantity INTEGER, price TEXT)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders
(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, quantity INTEGER, price TEXT, phone TEXT, location TEXT, order_date TEXT)
''')
conn.commit()

def is_working_hours():
    now = datetime.now().time()
    start_time = datetime.strptime("09:00", "%H:%M").time()
    end_time = datetime.strptime("23:00", "%H:%M").time()
    return start_time <= now <= end_time

def create_main_menu(message, language):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    if message.chat.id in ADMIN_CHAT_IDS:
        markup = create_admin_menu(message)
    else:
        menu_button = types.KeyboardButton("📜 Menyu" if language == "🇺🇿 O'zbek" else "📜 Меню")
        contact_button = types.KeyboardButton("☎️ Kontakt" if language == "🇺🇿 O'zbek" else "☎️ Контакт")
        order_button = types.KeyboardButton("🚖 Buyurtma" if language == "🇺🇿 O'zbek" else "🚖 Заказ")
        cart_button = types.KeyboardButton("🛒 Savatcha" if language == "🇺🇿 O'zbek" else "🛒 Корзина")
        settings_button = types.KeyboardButton("⚙️ Sozlamalar" if language == "🇺🇿 O'zbek" else "⚙️ Настройки")
        markup.add(menu_button, contact_button, order_button, cart_button, settings_button)
    return markup

def create_admin_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    send_message_button = types.KeyboardButton("📢 Habar yuborish" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📢 Отправить сообщение")
    add_button = types.KeyboardButton("🆕 Mahsulot qo'shish" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🆕 Добавить продукт")
    edit_button = types.KeyboardButton("✏️ Mahsulot tahrirlash" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "✏️ Редактировать продукт")
    delete_button = types.KeyboardButton("🗑️ Mahsulot o'chirish" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Удалить продукт")
    markup.add(send_message_button, add_button, edit_button, delete_button)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in ADMIN_CHAT_IDS:
        send_admin_menu(message)
    elif str(user_id) in user_data:
        send_main_menu(message)
    else:
        start_registration(message)

def start_registration(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    uzb_button = types.KeyboardButton("🇺🇿 O'zbek")
    rus_button = types.KeyboardButton("🇷🇺 русский")
    markup.add(uzb_button, rus_button)
    msg = bot.reply_to(message, "Tilni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_language_step)

def process_language_step(message):
    language = message.text
    if language not in ["🇺🇿 O'zbek", "🇷🇺 русский"]:
        msg = bot.reply_to(message, "Iltimos, tilni tanlang:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton("🇺🇿 O'zbek"), types.KeyboardButton("🇷🇺 русский")))
        bot.register_next_step_handler(msg, process_language_step)
    else:
        user_data[message.chat.id] = {"language": language}
        save_user_data(user_data)
        msg = bot.reply_to(message, "Ismingizni kiriting:" if language == "🇺🇿 O'zbek" else "Введите ваше имя:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_name_step, language)

def process_name_step(message, language):
    name = message.text
    if not name.isalpha():
        msg = bot.reply_to(message, "Iltimos, to'g'ri ismingizni kiriting:" if language == "🇺🇿 O'zbek" else "Пожалуйста, введите правильное имя:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_name_step, language)
    else:
        user_data[message.chat.id]["name"] = name
        save_user_data(user_data)
        msg = bot.reply_to(message, "Telefon raqamingizni kiriting: +998XXXXXXXXX" if language == "🇺🇿 O'zbek" else "Введите ваш номер телефона: +998XXXXXXXXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_phone_step, language)

def process_phone_step(message, language):
    phone = message.text
    if not phone.startswith("+998") or not phone[4:].isdigit() or len(phone) != 13:
        msg = bot.reply_to(message, "Iltimos, to'g'ri telefon raqamini kiriting: +998XXXXXXXXX" if language == "🇺🇿 O'zbek" else "Пожалуйста, введите правильный номер телефона: +998XXXXXXXXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_phone_step, language)
    else:
        user_data[message.chat.id]["phone"] = phone
        save_user_data(user_data)
        msg = bot.reply_to(message, "Lokatsiyani jo'nating:" if language == "🇺🇿 O'zbek" else "Отправьте ваше местоположение:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('📍 Lakatsiyani yuboring' if language == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True)))
        bot.register_next_step_handler(msg, process_location_step, language)

def process_location_step(message, language):
    if not message.location:
        msg = bot.reply_to(message, "Iltimos, lokatsiyani jo'nating:" if language == "🇺🇿 O'zbek" else "Пожалуйста, отправьте ваше местоположение:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('📍 Lakatsiyani yuboring' if language == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True)))
        bot.register_next_step_handler(msg, process_location_step, language)
    else:
        location = f"{message.location.latitude},{message.location.longitude}"
        user_data[message.chat.id]["location"] = location
        save_user_data(user_data)
        bot.reply_to(message, "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!" if language == "🇺🇿 O'zbek" else "Регистрация успешно завершена!", reply_markup=create_main_menu(message, language))
        send_main_menu(message)

def send_main_menu(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = create_main_menu(message, language)
    bot.send_message(message.chat.id, "Asosiy menyu:" if language == "🇺🇿 O'zbek" else "Главное меню:", reply_markup=markup)

# Admin menyu
@bot.message_handler(commands=['admin'])
def send_admin_menu(message):
    if message.chat.id in ADMIN_CHAT_IDS:
        markup = create_admin_menu(message)
        bot.reply_to(message, "Admin menyusi" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Админ меню", reply_markup=markup)
    else:
        bot.reply_to(message, "Siz admin emassiz." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Вы не администратор.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "📢 Habar yuborish" and message.chat.id in ADMIN_CHAT_IDS)
def send_message(message):
    msg = bot.reply_to(message, "Iltimos habarni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Введите сообщение:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_send_message)

def process_send_message(message):
    for user_id in user_data.keys():
        try:
            bot.send_message(user_id, message.text)
        except:
            continue
    bot.reply_to(message, "Habar yuborildi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Сообщение отправлено.", reply_markup=create_admin_menu(message))

# Add product
@bot.message_handler(func=lambda message: message.text == "🆕 Mahsulot qo'shish" and message.chat.id in ADMIN_CHAT_IDS)
def add_product(message):
    msg = bot.reply_to(message, "📝 Mahsulot nomini kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите название продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_name_step)

def process_product_name_step(message):
    product_name = message.text
    msg = bot.reply_to(message, "📸 Mahsulot rasmini yuboring:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📸 Отправьте изображение продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_image_step, product_name)

def process_product_image_step(message, product_name):
    if message.text == '/skip':
        product_image = None
    else:
        product_image = message.photo[-1].file_id
    msg = bot.reply_to(message, "💰 Mahsulotni birinchi narxini kiriting: (xxx.xxx)" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите первую цену продукта: (xxx.xxx)", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_first_price_step, product_name, product_image)

def process_product_first_price_step(message, product_name, product_image):
    product_first_price = message.text  # String sifatida saqlanadi
    msg = bot.reply_to(message, "💰 Mahsulotni ikkinchi narxini kiriting: (xxx.xxx) yoki /skip bosing:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите вторую цену продукта: (xxx.xxx) или нажмите /skip:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_product_second_price_step, product_name, product_image, product_first_price)

def process_product_second_price_step(message, product_name, product_image, product_first_price):
    if message.text == '/skip':
        product_second_price = None
    else:
        product_second_price = message.text  # String sifatida saqlanadi
    msg = bot.reply_to(message, "🍽 Mahsulot turini tanlang:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🍽 Выберите категорию продукта:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True).add(
        types.KeyboardButton("🥗 Birinchi ovqat"), types.KeyboardButton("🍛 Ikkinchi ovqat"), types.KeyboardButton("🥗 Salat"), types.KeyboardButton("🍱 Setlar"), types.KeyboardButton("🥤 Ichimliklar")
    ))
    bot.register_next_step_handler(msg, process_product_category_step, product_name, product_image, product_first_price, product_second_price)

def process_product_category_step(message, product_name, product_image, product_first_price, product_second_price):
    product_category = message.text
    cursor.execute("INSERT INTO products (name, price, net_price, image, category) VALUES (?, ?, ?, ?, ?)",
                   (product_name, product_first_price, product_second_price, product_image, product_category))
    conn.commit()
    second_price_info = f" - {product_second_price}" if product_second_price else ""
    bot.reply_to(message, f"✅ Mahsulot qo'shildi: {product_name} - {product_first_price}{second_price_info}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Продукт добавлен: {product_name} - {product_first_price}{second_price_info}", reply_markup=create_admin_menu(message))

@bot.message_handler(func=lambda message: message.text == "✏️ Mahsulot tahrirlash" and message.chat.id in ADMIN_CHAT_IDS)
def edit_product(message):
    product_list = "\n".join([f"{row[0]}: {row[1]}" for row in cursor.execute("SELECT id, name FROM products")])
    if not product_list:
        bot.reply_to(message, "❌ Hozircha mahsulotlar mavjud emas." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ На данный момент продуктов нет.", reply_markup=create_admin_menu(message))
        return
    msg = bot.reply_to(message, f"📋 Mahsulotlar ro'yxati:\n{product_list}\n🔢 Mahsulot IDsini kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"📋 Список продуктов:\n{product_list}\n🔢 Введите ID продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_edit_product_id_step)

def process_edit_product_id_step(message):
    try:
        product_id = int(message.text)
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        if not product:
            bot.reply_to(message, "❌ Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Продукт не найден.", reply_markup=create_admin_menu(message))
            return
    except ValueError:
        bot.reply_to(message, "❌ Iltimos, to'g'ri ID kiriting." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, введите правильный ID.", reply_markup=create_admin_menu(message))
        return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("📝 Yangi nomni kiriting" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите новое название")
    edit_price_button = types.KeyboardButton("💰 Yangi narxni kiriting" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите новую цену")
    markup.add(edit_name_button, edit_price_button)
    msg = bot.reply_to(message, "✏️ Tahrirlash variantini tanlang:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "✏️ Выберите вариант редактирования:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_edit_option_step, product_id)

def process_edit_option_step(message, product_id):
    if message.text == ("📝 Yangi nomni kiriting" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите новое название"):
        msg = bot.reply_to(message, "📝 Yangi nomni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите новое название:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_edit_product_name, product_id)
    elif message.text == ("💰 Yangi narxni kiriting" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите новую цену"):
        msg = bot.reply_to(message, "💰 Yangi narxni kiriting: XXX.XXX" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите новую цену: XXX.XXX", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, process_edit_product_price, product_id)
    else:
        bot.reply_to(message, "❌ Iltimos, tahrirlash variantini tanlang." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, выберите вариант редактирования.", reply_markup=create_admin_menu(message))

def process_edit_product_name(message, product_id):
    new_name = message.text
    cursor.execute("UPDATE products SET name = ? WHERE id = ?", (new_name, product_id))
    conn.commit()
    bot.reply_to(message, f"✅ Mahsulot nomi yangilandi: {new_name}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Название продукта обновлено: {new_name}", reply_markup=create_admin_menu(message))

def process_edit_product_price(message, product_id):
    new_price = message.text  # String sifatida saqlanadi
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()
    bot.reply_to(message, f"✅ Mahsulot narxi yangilandi: {new_price}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Цена продукта обновлена: {new_price}", reply_markup=create_admin_menu(message))

@bot.message_handler(func=lambda message: message.text == "🗑️ Mahsulot o'chirish" and message.chat.id in ADMIN_CHAT_IDS)
def delete_product(message):
    product_list = "\n".join([f"{row[0]}: {row[1]}" for row in cursor.execute("SELECT id, name FROM products")])
    if not product_list:
        bot.reply_to(message, "❌ Hozircha mahsulotlar mavjud emas." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ На данный момент продуктов нет.", reply_markup=create_admin_menu(message))
        return
    msg = bot.reply_to(message, f"📋 Mahsulotlar ro'yxati:\n{product_list}\n🔢 Mahsulot IDsini kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"📋 Список продуктов:\n{product_list}\n🔢 Введите ID продукта:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_delete_product_id_step)

def process_delete_product_id_step(message):
    try:
        product_id = int(message.text)
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        bot.reply_to(message, f"✅ Mahsulot o'chirildi: ID {product_id}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Продукт удален: ID {product_id}", reply_markup=create_admin_menu(message))
    except ValueError:
        bot.reply_to(message, "❌ Iltimos, to'g'ri ID kiriting." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, введите правильный ID.", reply_markup=create_admin_menu(message))

# Main menyu
@bot.message_handler(func=lambda message: message.text == "📜 Menyu" or message.text == "📜 Меню")
def show_menu(message):
    language = user_data[str(message.chat.id)]["language"]
    categories = ["🥗 Birinchi ovqat", "🍛 Ikkinchi ovqat", "🥗 Salat", "🍱 Setlar", "🥤 Ichimliklar"]
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in categories:
        markup.add(types.KeyboardButton(category))
    markup.add(types.KeyboardButton("🏠 Asosiy menyu" if language == "🇺🇿 O'zbek" else "🏠 Главное меню"))

    msg = bot.reply_to(message, "🍽 Bo'limni tanlang:" if language == "🇺🇿 O'zbek" else "🍽 Выберите категорию:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_category_items)

def show_category_items(message):
    if message.text == "🏠 Asosiy menyu" or message.text == "🏠 Главное меню":
        send_main_menu(message)
        return
    
    category = message.text
    cursor.execute("SELECT name FROM products WHERE category = ?", (category,))
    items = cursor.fetchall()
    
    if not items:
        bot.reply_to(message, "❌ Bu bo'limda hech narsa yo'q." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ В этой категории пока ничего нет.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for item in items:
        markup.add(types.KeyboardButton(item[0]))
    markup.add(types.KeyboardButton("📜 Menyu" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📜 Меню"))

    msg = bot.reply_to(message, "📋 Mahsulotni tanlang:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📋 Выберите продукт:", reply_markup=markup)
    bot.register_next_step_handler(msg, show_product_details)

def show_product_details(message):
    if message.text == "📜 Menyu" or message.text == "📜 Меню":
        show_menu(message)
        return

    product_name = message.text
    cursor.execute("SELECT * FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()
    if not product:
        bot.reply_to(message, "❌ Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Продукт не найден.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    user_states[message.chat.id] = {'product_id': product[0], 'quantity': 1}
    language = user_data[str(message.chat.id)]["language"]
    caption = f"{product[1]}\n\n{product[2]} so'm" if language == "🇺🇿 O'zbek" else f"{product[1]}\n\n{product[2]} сум"
    if product[3]:
        caption += f" - {product[3]} so'm" if language == "🇺🇿 O'zbek" else f" - {product[3]} сум"
    
    if product[4]:
        bot.send_photo(message.chat.id, product[4], caption=caption)
    else:
        bot.send_message(message.chat.id, caption)
    
    show_price_buttons(message, product[2], product[3])

def show_price_buttons(message, price, net_price):
    language = user_data[str(message.chat.id)]["language"]
    markup = types.InlineKeyboardMarkup()
    if net_price:
        markup.add(types.InlineKeyboardButton(text=f"{price} so'm" if language == "🇺🇿 O'zbek" else f"{price} сум", callback_data=f"select_price:{price}"),
                   types.InlineKeyboardButton(text=f"{net_price} so'm" if language == "🇺🇿 O'zbek" else f"{net_price} сум", callback_data=f"select_net_price:{net_price}"))
    else:
        markup.add(types.InlineKeyboardButton(text=f"{price} so'm" if language == "🇺🇿 O'zbek" else f"{price} сум", callback_data=f"select_price:{price}"))
    bot.send_message(message.chat.id, f"💰 Narxni tanlang:" if language == "🇺🇿 O'zbek" else "💰 Выберите цену:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_price") or call.data.startswith("select_net_price"))
def callback_select_price(call):
    price = call.data.split(":")[1]
    user_states[call.message.chat.id]['selected_price'] = price
    update_quantity_message(call.message)

def update_quantity_message(message):
    state = user_states[message.chat.id]
    language = user_data[str(message.chat.id)]["language"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="➖", callback_data="decrease"),
               types.InlineKeyboardButton(text=str(state['quantity']), callback_data="quantity"),
               types.InlineKeyboardButton(text="➕", callback_data="increase"))
    markup.add(types.InlineKeyboardButton(text="➕ Qo'shish" if language == "🇺🇿 O'zbek" else "➕ Добавить", callback_data="add_to_cart"),
               types.InlineKeyboardButton(text="❌ Bekor qilish" if language == "🇺🇿 O'zbek" else "❌ Отмена", callback_data="cancel"))
    bot.send_message(message.chat.id, f"Nechta buyurtma qilasiz?" if language == "🇺🇿 O'zbek" else f"Сколько хотите заказать?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["decrease", "increase", "add_to_cart", "cancel"])
def callback_inline(call):
    state = user_states[call.message.chat.id]
    if call.data in ["decrease", "increase"]:
        if call.data == "decrease" and state['quantity'] > 1:
            state['quantity'] -= 1
        elif call.data == "increase":
            state['quantity'] += 1
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=update_quantity_markup(state['quantity'], call.message.chat.id))
    elif call.data == "add_to_cart":
        selected_price = state.get('selected_price', None)
        if selected_price is None:
            bot.answer_callback_query(call.id, "Iltimos, narxni tanlang" if user_data[str(call.message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Пожалуйста, выберите цену")
            return
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", 
                       (call.message.chat.id, state['product_id'], state['quantity'], selected_price))
        conn.commit()
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"🛒 Savatingizga qo'shildi: {state['quantity']} dona" if user_data[str(call.message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"🛒 Добавлено в корзину: {state['quantity']} шт")
    elif call.data == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="❌ Bekor qilindi" if user_data[str(call.message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Отменено")

def update_quantity_markup(quantity, chat_id):
    language = user_data[str(chat_id)]["language"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="➖", callback_data="decrease"),
               types.InlineKeyboardButton(text=str(quantity), callback_data="quantity"),
               types.InlineKeyboardButton(text="➕", callback_data="increase"))
    markup.add(types.InlineKeyboardButton(text="➕ Qo'shish" if language == "🇺🇿 O'zbek" else "➕ Добавить", callback_data="add_to_cart"),
               types.InlineKeyboardButton(text="❌ Bekor qilish" if language == "🇺🇿 O'zbek" else "❌ Отмена", callback_data="cancel"))
    return markup

# Show contact
@bot.message_handler(func=lambda message: message.text == "☎️ Kontakt" or message.text == "☎️ Контакт")
def show_contact(message):
    bot.reply_to(message, "📞 Murojaat uchun: +998 99 640 33 37" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📞 Контакты: +998 99 640 33 37\n@roziboyevdev", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "🚖 Buyurtma" or message.text == "🚖 Заказ")
def place_order(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "🛒 Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина пуста.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    if not is_working_hours():
        bot.reply_to(message, "🕒 Ish vaqti 09:00dan 23:00gacha" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🕒 Рабочее время с 09:00 до 23:00", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    msg = bot.reply_to(message, "📞 Telefon raqamingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📞 Введите ваш номер телефона:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, get_phone_number)

def get_phone_number(message):
    phone_number = message.text
    msg = bot.reply_to(message, "📍 Lokatsiyangizni jo'nating:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📍 Отправьте ваше местоположение:", reply_markup=types.ReplyKeyboardMarkup(one_time_keyboard=True).add(types.KeyboardButton('📍 Lakatsiyani yuboring' if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True)))
    bot.register_next_step_handler(msg, get_location, phone_number)

def get_location(message, phone_number):
    if not message.location:
        bot.reply_to(message, "❌ Iltimos, lokatsiyani jo'nating." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, отправьте ваше местоположение.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    location = f"{message.location.latitude},{message.location.longitude}"
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()

    order_message = "🆕 Yangi buyurtma:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🆕 Новый заказ:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * float(item[2].replace(',', ''))
        order_message += f"{item[0]} : {item[1]} x {item[2]} so'm = {item_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} : {item[1]} x {item[2]} сум = {item_price:,.0f} сум\n"
        total_price += item_price
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, price, phone, location, order_date) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, item[1], item[2], phone_number, location, datetime.now().strftime('%Y-%m-%d')))
    order_message += f"💵 Jami: {total_price:,.0f} so'm\n📞 Telefon: {phone_number}\n📍 Lokatsiya: {location}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"💵 Итого: {total_price:,.0f} сум\n📞 Телефон: {phone_number}\n📍 Местоположение: {location}"
    conn.commit()
    bot.send_message(ORDER_GROUP_ID, order_message)
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "✅ Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz siz bilan bog'lanadi!" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "✅ Ваш заказ принят! Операторы свяжутся с вами в ближайшее время!", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "🛒 Savatcha" or message.text == "🛒 Корзина")
def show_cart(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.reply_to(message, "🛒 Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина пуста.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    cart_message = "🛒 Sizning savatingiz:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * float(item[2].replace(',', ''))
        cart_message += f"{item[0]} : {item[1]} x {item[2]} so'm = {item_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} : {item[1]} x {item[2]} сум = {item_price:,.0f} сум\n"
        total_price += item_price
    cart_message += f"💵 Jami: {total_price:,.0f} so'm" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"💵 Итого: {total_price:,.0f} сум"
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🚖 Buyurtma" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🚖 Заказ"),
               types.KeyboardButton("🗑️ Savatchani tozalash" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Очистить корзину"))
    markup.add(types.KeyboardButton("🕒 Tarix" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🕒 История"))
    markup.add(types.KeyboardButton("🏠 Asosiy menyu" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🏠 Главное меню"))
    
    bot.send_message(message.chat.id, cart_message, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🗑️ Savatchani tozalash" or message.text == "🗑️ Очистить корзину")
def clear_cart(message):
    user_id = message.from_user.id
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.reply_to(message, "🗑️ Savatcha tozalandi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Корзина очищена.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "🕒 Tarix" or message.text == "🕒 История")
def show_order_history(message):
    user_id = message.from_user.id
    cursor.execute("SELECT orders.order_date, products.name, orders.quantity, orders.price FROM orders JOIN products ON orders.product_id = products.id WHERE orders.user_id = ?", (user_id,))
    order_items = cursor.fetchall()
    if not order_items:
        bot.reply_to(message, "📋 Siz hali hech narsa buyurtma qilganingiz yuq!" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📋 У вас пока нет истории заказов.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return

    history_message = "🕒 Buyurtmalar tarixi:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🕒 История заказов:\n"
    for item in order_items:
        total_price = item[2] * float(item[3].replace(',', ''))
        history_message += f"{item[0]} - {item[1]}: {item[2]} x {item[3]} so'm = {total_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} - {item[1]}: {item[2]} x {item[3]} сум = {total_price:,.0f} сум\n"

    bot.send_message(message.chat.id, history_message, reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))

@bot.message_handler(func=lambda message: message.text == "⚙️ Sozlamalar" or message.text == "⚙️ Настройки")
def show_settings(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("📝 Ismni o'zgartirish" if language == "🇺🇿 O'zbek" else "📝 Изменить имя")
    change_language_button = types.KeyboardButton("🌐 Tilni o'zgartirish" if language == "🇺🇿 O'zbek" else "🌐 Изменить язык")
    markup.add(edit_name_button, change_language_button)
    msg = bot.reply_to(message, "⚙️ Sozlamalar:" if language == "🇺🇿 O'zbek" else "⚙️ Настройки:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_settings)

def process_settings(message):
    language = user_data[str(message.chat.id)]["language"]
    if message.text == "📝 Ismni o'zgartirish" or message.text == "📝 Изменить имя":
        msg = bot.reply_to(message, "📝 Yangi ismingizni kiriting:" if language == "🇺🇿 O'zbek" else "📝 Введите ваше новое имя:", reply_markup=types.ForceReply())
        bot.register_next_step_handler(msg, change_name)
    elif message.text == "🌐 Tilni o'zgartirish" or message.text == "🌐 Изменить язык":
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        uzb_button = types.KeyboardButton("🇺🇿 O'zbek")
        rus_button = types.KeyboardButton("🇷🇺 русский")
        markup.add(uzb_button, rus_button)
        msg = bot.reply_to(message, "🌐 Tilni tanlang:" if language == "🇺🇿 O'zbek" else "🌐 Выберите язык:", reply_markup=markup)
        bot.register_next_step_handler(msg, change_language)

def change_name(message):
    new_name = message.text
    user_id = message.from_user.id
    user_data[str(user_id)]["name"] = new_name
    save_user_data(user_data)
    bot.reply_to(message, f"✅ Ismingiz o'zgartirildi: {new_name}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Ваше имя изменено: {new_name}", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))

def change_language(message):
    new_language = message.text
    if new_language not in ["🇺🇿 O'zbek", "🇷🇺 русский"]:
        bot.reply_to(message, "❌ Iltimos, tilni tanlang." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, выберите язык.", reply_markup=create_main_menu(message, user_data[str(message.chat.id)]["language"]))
        return
    user_id = message.from_user.id
    user_data[str(user_id)]["language"] = new_language
    save_user_data(user_data)
    bot.reply_to(message, f"✅ Til o'zgartirildi: {new_language}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Язык изменен: {new_language}", reply_markup=create_main_menu(message, new_language))

bot.infinity_polling()
