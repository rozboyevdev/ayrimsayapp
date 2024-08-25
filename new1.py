import json
import sqlite3
from telebot import TeleBot, types
from datetime import datetime

API_TOKEN = "7158602292:AAE9x3Lu-8iRdgi-o8CMfdbxFA649RN4Y5I"
ADMIN_CHAT_IDS = [1593464245]  # Admin chat ID'sini kiriting
ORDER_GROUP_ID = -1002165519452  # Buyurtmalarni yuboradigan guruh ID'sini kiriting

bot = TeleBot(API_TOKEN)

USER_DATA_FILE = 'users.json'
PRODUCT_IMAGE_DIR = 'product_images/'

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

conn = sqlite3.connect('restaurant.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS products
(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, net_price REAL, image TEXT, category TEXT)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS cart
(user_id INTEGER, product_id INTEGER, quantity INTEGER, price REAL)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders
(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, quantity INTEGER, phone TEXT, location TEXT)
''')
conn.commit()

def is_working_hours():
    now = datetime.now().time()
    start_time = datetime.strptime("09:00", "%H:%M").time()
    end_time = datetime.strptime("23:00", "%H:%M").time()
    return start_time <= now <= end_time

def create_main_menu(language):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    menu_button = types.KeyboardButton("📜 Menyu" if language == "🇺🇿 O'zbek" else "📜 Меню")
    contact_button = types.KeyboardButton("☎️ Kontakt" if language == "🇺🇿 O'zbek" else "☎️ Контакт")
    order_button = types.KeyboardButton("🚖 Buyurtma" if language == "🇺🇿 O'zbek" else "🚖 Заказ")
    cart_button = types.KeyboardButton("🛒 Savatcha" if language == "🇺🇿 O'zbek" else "🛒 Корзина")
    settings_button = types.KeyboardButton("⚙️ Sozlamalar" if language == "🇺🇿 O'zbek" else "⚙️ Настройки")
    markup.add(menu_button, contact_button, order_button, cart_button, settings_button)
    return markup

def create_admin_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("📢 Habar yuborish"))
    markup.add(types.KeyboardButton("🆕 Mahsulot qo'shish"))
    markup.add(types.KeyboardButton("✏️ Mahsulotni tahrirlash"))
    markup.add(types.KeyboardButton("🗑️ Mahsulot o'chirish"))
    markup.add(types.KeyboardButton("🔙 Asosiy"))
    return markup

# START command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if str(user_id) in user_data:
        send_main_menu(message)
    else:
        start_registration(message)

# Menyu command
@bot.message_handler(func=lambda message: message.text in ["📜 Menyu", "📜 Меню"])
def show_menu(message):
    language = user_data[str(message.chat.id)]["language"]
    categories = ["🥗 Birinchi ovqat", "🍛 Ikkinchi ovqat", "🥗 Salat", "🍱 Setlar"]

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in categories:
        markup.add(types.KeyboardButton(category))
    markup.add(types.KeyboardButton("🏠 Asosiy menyu" if language == "🇺🇿 O'zbek" else "🏠 Главное меню"))

    bot.send_message(message.chat.id, "🍽 Bo'limni tanlang:" if language == "🇺🇿 O'zbek" else "🍽 Выберите категорию:", reply_markup=markup)

# Show products in category
@bot.message_handler(func=lambda message: message.text in ["🥗 Birinchi ovqat", "🍛 Ikkinchi ovqat", "🥗 Salat", "🍱 Setlar"])
def show_category_items(message):
    category = message.text
    cursor.execute("SELECT name FROM products WHERE category = ?", (category,))
    items = cursor.fetchall()

    if not items:
        bot.send_message(message.chat.id, "❌ Bu bo'limda hech narsa yo'q." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ В этой категории пока ничего нет.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for item in items:
        markup.add(types.KeyboardButton(item[0]))
    markup.add(types.KeyboardButton("📜 Menyu" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📜 Меню"))

    bot.send_message(message.chat.id, "📋 Mahsulotni tanlang:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📋 Выберите продукт:", reply_markup=markup)

# Return to main menu
@bot.message_handler(func=lambda message: message.text in ["🏠 Asosiy menyu", "🏠 Главное меню"])
def return_to_main_menu(message):
    send_main_menu(message)

# Admin command
@bot.message_handler(commands=['admin'])
def send_admin_menu(message):
    if message.chat.id in ADMIN_CHAT_IDS:
        markup = create_admin_menu()
        bot.send_message(message.chat.id, "Admin menyusi", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Siz admin emassiz.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

# Show product details
@bot.message_handler(func=lambda message: message.text not in ["📜 Menyu", "📜 Меню", "🏠 Asosiy menyu", "🏠 Главное меню", "☎️ Kontakt", "☎️ Контакт", "🚖 Buyurtma", "🚖 Заказ", "🛒 Savatcha", "🛒 Корзина", "⚙️ Sozlamalar", "⚙️ Настройки"])
def show_product_details(message):
    product_name = message.text
    cursor.execute("SELECT * FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()
    
    if not product:
        bot.send_message(message.chat.id, "❌ Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Продукт не найден.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    # Mahsulot ID va boshqa ma'lumotlarni user_data ga saqlash
    user_data[str(message.chat.id)]['product_id'] = product[0]
    user_data[str(message.chat.id)]['quantity'] = 1  # Boshlang'ich qiymat sifatida 1

    language = user_data[str(message.chat.id)]["language"]
    caption = f"{product[1]}\n\n{product[2]:,.0f} so'm" if language == "🇺🇿 O'zbek" else f"{product[1]}\n\n{product[2]:,.0f} сум"
    if product[3]:  # Agar mahsulotda net_price bo'lsa, qo'shib ko'rsatiladi
        caption += f" - {product[3]:,.0f} so'm" if language == "🇺🇿 O'zbek" else f" - {product[3]:,.0f} сум"

    try:
        images = json.loads(product[4]) if product[4] else []
    except json.JSONDecodeError:
        images = []

    if images:
        media = [types.InputMediaPhoto(img_id, caption=caption if i == 0 else "") for i, img_id in enumerate(images)]
        bot.send_media_group(message.chat.id, media)
    else:
        bot.send_message(message.chat.id, caption)

    show_price_buttons(message, product[2], product[3])

def show_price_buttons(message, price, net_price):
    language = user_data[str(message.chat.id)]["language"]
    markup = types.InlineKeyboardMarkup()
    
    if net_price:
        markup.add(types.InlineKeyboardButton(text=f"{price:,.0f} so'm" if language == "🇺🇿 O'zbek" else f"{price:,.0f} сум", callback_data=f"select_price:{price}"),
                   types.InlineKeyboardButton(text=f"{net_price:,.0f} so'm" if language == "🇺🇿 O'zbek" else f"{net_price:,.0f} сум", callback_data=f"select_net_price:{net_price}"))
    else:
        markup.add(types.InlineKeyboardButton(text=f"{price:,.0f} so'm" if language == "🇺🇿 O'zbek" else f"{price:,.0f} сум", callback_data=f"select_price:{price}"))
    
    bot.send_message(message.chat.id, f"💰 Narxni tanlang:" if language == "🇺🇿 O'zbek" else "💰 Выберите цену:", reply_markup=markup)

# Handle price selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_price") or call.data.startswith("select_net_price"))
def callback_select_price(call):
    price = float(call.data.split(":")[1])
    
    # Tanlangan narxni saqlash
    user_data[str(call.message.chat.id)]['selected_price'] = price
    
    bot.answer_callback_query(call.id)
    update_quantity_message(call.message, call.message.chat.id, 1)

def update_quantity_message(message, chat_id, quantity):
    language = user_data[str(chat_id)]["language"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="➖", callback_data="decrease"),
               types.InlineKeyboardButton(text=str(quantity), callback_data="quantity"),
               types.InlineKeyboardButton(text="➕", callback_data="increase"))
    markup.add(types.InlineKeyboardButton(text="➕ Qo'shish" if language == "🇺🇿 O'zbek" else "➕ Добавить", callback_data="add_to_cart"),
               types.InlineKeyboardButton(text="❌ Bekor qilish" if language == "🇺🇿 O'zbek" else "❌ Отмена", callback_data="cancel"))
    
    bot.edit_message_text(f"Nechta buyurtma qilasiz?" if language == "🇺🇿 O'zbek" else f"Сколько хотите заказать?", chat_id=chat_id, message_id=message.message_id, reply_markup=markup)

# Handle cart operations
@bot.callback_query_handler(func=lambda call: call.data in ["decrease", "increase", "add_to_cart", "cancel"])
def callback_inline(call):
    user_id = call.message.chat.id
    language = user_data[str(user_id)]["language"]

    # `product_id` mavjudligini tekshirish
    if 'product_id' not in user_data[str(user_id)]:
        bot.send_message(user_id, "❌ Mahsulotni tanlang." if language == "🇺🇿 O'zbek" else "❌ Пожалуйста, выберите продукт.")
        return
    
    if call.data == "decrease" and user_data[str(user_id)].get('quantity', 1) > 1:
        user_data[str(user_id)]['quantity'] -= 1
    elif call.data == "increase":
        user_data[str(user_id)]['quantity'] = user_data[str(user_id)].get('quantity', 1) + 1
    elif call.data == "add_to_cart":
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                       (user_id, user_data[str(user_id)]['product_id'], user_data[str(user_id)]['quantity'], user_data[str(user_id)].get('selected_price')))
        conn.commit()
        bot.edit_message_text(f"🛒 Savatingizga qo'shildi: {user_data[str(user_id)]['quantity']} dona" if language == "🇺🇿 O'zbek" else f"🛒 Добавлено в корзину: {user_data[str(user_id)]['quantity']} шт", chat_id=user_id, message_id=call.message.message_id)
        show_menu(call.message)
        return
    elif call.data == "cancel":
        bot.edit_message_text("❌ Bekor qilindi" if language == "🇺🇿 O'zbek" else "❌ Отменено", chat_id=user_id, message_id=call.message.message_id)
        show_menu(call.message)
        return

    update_quantity_message(call.message, user_id, user_data[str(user_id)].get('quantity', 1))

# Show cart
@bot.message_handler(func=lambda message: message.text in ["🛒 Savatcha", "🛒 Корзина"])
def show_cart(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.send_message(message.chat.id, "🛒 Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    cart_message = "🛒 Sizning savatingiz:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        cart_message += f"{item[0]} : {item[1]} x {item[2]:,.0f} so'm = {item_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} : {item[1]} x {item[2]:,.0f} сум = {item_price:,.0f} сум\n"
        total_price += item_price
    cart_message += f"💵 Jami: {total_price:,.0f} so'm" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"💵 Итого: {total_price:,.0f} сум"

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton("🚖 Buyurtma qilish" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🚖 Заказ"),
               types.KeyboardButton("🗑️ Savatchani tozalash" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Очистить корзину"))
    markup.add(types.KeyboardButton("🏠 Asosiy menyu" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🏠 Главное меню"))

    bot.send_message(message.chat.id, cart_message, reply_markup=markup)

# Place order
@bot.message_handler(func=lambda message: message.text in ["🚖 Buyurtma qilish", "🚖 Заказ"])
def place_order(message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        bot.send_message(message.chat.id, "🛒 Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    if not is_working_hours():
        bot.send_message(message.chat.id, "🕒 Ish vaqti 09:00dan 23:00gacha" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🕒 Рабочее время с 09:00 до 23:00", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    bot.send_message(message.chat.id, "📞 Telefon raqamingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📞 Введите ваш номер телефона:")
    bot.register_next_step_handler(message, get_phone_number)

def get_phone_number(message):
    phone_number = message.text
    user_data[str(message.chat.id)]["phone_number"] = phone_number
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('📍 Lakatsiyani yuboring' if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True))
    bot.send_message(message.chat.id, "📍 Lokatsiyangizni jo'nating:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📍 Отправьте ваше местоположение:", reply_markup=markup)
    bot.register_next_step_handler(message, get_location)

def get_location(message):
    if not message.location:
        bot.send_message(message.chat.id, "❌ Iltimos, lokatsiyani jo'nating." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, отправьте ваше местоположение.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    location = f"{message.location.latitude},{message.location.longitude}"
    user_data[str(message.chat.id)]["location"] = location
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()

    order_message = "🆕 Yangi buyurtma:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🆕 Новый заказ:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        order_message += f"{item[0]} : {item[1]} x {item[2]:,.0f} so'm = {item_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} : {item[1]} x {item[2]:,.0f} сум = {item_price:,.0f} сум\n"
        total_price += item_price
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, phone, location) VALUES (?, ?, ?, ?, ?)", (user_id, item[1], item[2], user_data[str(message.chat.id)]["phone_number"], location))
    order_message += f"💵 Jami: {total_price:,.0f} so'm\n📞 Telefon: {user_data[str(message.chat.id)]['phone_number']}\n📍 Lokatsiya: {location}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"💵 Итого: {total_price:,.0f} сум\n📞 Телефон: {user_data[str(message.chat.id)]['phone_number']}\n📍 Местоположение: {location}"
    conn.commit()
    bot.send_message(ORDER_GROUP_ID, order_message)
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz siz bilan bog'lanadi!" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "✅ Ваш заказ принят! Операторы свяжутся с вами в ближайшее время!", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

# Clear cart
@bot.message_handler(func=lambda message: message.text in ["🗑️ Savatchani tozalash", "🗑️ Очистить корзину"])
def clear_cart(message):
    user_id = message.from_user.id
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    bot.send_message(message.chat.id, "🗑️ Savatcha tozalandi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Корзина очищена.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

# Contact info
@bot.message_handler(func=lambda message: message.text in ["☎️ Kontakt", "☎️ Контакт"])
def show_contact(message):
    bot.send_message(message.chat.id, "📞 Murojaat uchun: +998 99 640 33 37\n@roziboyevdev" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📞 Контакты: +998 99 640 33 37\n@roziboyevdev", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

# Settings menu
@bot.message_handler(func=lambda message: message.text in ["⚙️ Sozlamalar", "⚙️ Настройки"])
def show_settings(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = types.KeyboardButton("📝 Ismni o'zgartirish" if language == "🇺🇿 O'zbek" else "📝 Изменить имя")
    change_language_button = types.KeyboardButton("🌐 Tilni o'zgartirish" if language == "🇺🇿 O'zbek" else "🌐 Изменить язык")
    back_button = types.KeyboardButton("🏠 Asosiy menyu" if language == "🇺🇿 O'zbek" else "🏠 Главное меню")
    markup.add(edit_name_button, change_language_button, back_button)
    bot.send_message(message.chat.id, "⚙️ Sozlamalar:" if language == "🇺🇿 O'zbek" else "⚙️ Настройки:", reply_markup=markup)

# Change name
@bot.message_handler(func=lambda message: message.text in ["📝 Ismni o'zgartirish", "📝 Изменить имя"])
def change_name(message):
    bot.send_message(message.chat.id, "📝 Yangi ismingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите ваше новое имя:")
    bot.register_next_step_handler(message, update_name)

def update_name(message):
    new_name = message.text
    user_id = message.from_user.id
    user_data[str(user_id)]["name"] = new_name
    save_user_data(user_data)
    bot.send_message(message.chat.id, f"✅ Ismingiz o'zgartirildi: {new_name}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Ваше имя изменено: {new_name}", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

# Change language
@bot.message_handler(func=lambda message: message.text in ["🌐 Tilni o'zgartirish", "🌐 Изменить язык"])
def change_language(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    uzb_button = types.KeyboardButton("🇺🇿 O'zbek")
    rus_button = types.KeyboardButton("🇷🇺 русский")
    markup.add(uzb_button, rus_button)
    bot.send_message(message.chat.id, "🌐 Tilni tanlang:" if language == "🇺🇿 O'zbek" else "🌐 Выберите язык:", reply_markup=markup)
    bot.register_next_step_handler(message, update_language)

def update_language(message):
    new_language = message.text
    if new_language not in ["🇺🇿 O'zbek", "🇷🇺 русский"]:
        bot.send_message(message.chat.id, "❌ Iltimos, tilni tanlang." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, выберите язык.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return
    user_id = message.from_user.id
    user_data[str(user_id)]["language"] = new_language
    save_user_data(user_data)
    bot.send_message(message.chat.id, f"✅ Til o'zgartirxildi: {new_language}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Язык изменен: {new_language}", reply_markup=create_main_menu(new_language))

# Registration process
def start_registration(message):
    markup = types.ReplyKeyboardMarkup(onetime_keyboard=True, resize_keyboard=True)
    uzb_button = types.KeyboardButton("🇺🇿 O'zbek")
    rus_button = types.KeyboardButton("🇷🇺 русский")
    markup.add(uzb_button, rus_button)
    bot.send_message(message.chat.id, "Tilni tanlang:", reply_markup=markup)
    bot.register_next_step_handler(message, process_language_step)

def process_language_step(message):
    language = message.text
    if language not in ["🇺🇿 O'zbek", "🇷🇺 русский"]:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(types.KeyboardButton("🇺🇿 O'zbek"), types.KeyboardButton("🇷🇺 русский"))
        bot.send_message(message.chat.id, "Iltimos, tilni tanlang:", reply_markup=markup)
        return
    user_data[str(message.chat.id)]["language"] = language
    bot.send_message(message.chat.id, "Ismingizni kiriting:" if language == "🇺🇿 O'zbek" else "Введите ваше имя:")
    bot.register_next_step_handler(message, process_name_step)

def process_name_step(message):
    name = message.text
    if not name.isalpha():
        bot.send_message(message.chat.id, "Iltimos, to'g'ri ismingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Пожалуйста, введите правильное имя:")
        return
    user_data[str(message.chat.id)]["name"] = name
    bot.send_message(message.chat.id, "Telefon raqamingizni kiriting: +998XXXXXXXXX" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Введите ваш номер телефона: +998XXXXXXXXX")
    bot.register_next_step_handler(message, process_phone_step)

def process_phone_step(message):
    phone = message.text
    if not phone.startswith("+998") or not phone[4:].isdigit() or len(phone) != 13:
        bot.send_message(message.chat.id, "Iltimos, to'g'ri telefon raqamini kiriting: +998XXXXXXXXX" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Пожалуйста, введите правильный номер телефона: +998XXXXXXXXX")
        return
    user_data[str(message.chat.id)]["phone"] = phone
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton('📍 Lakatsiyani yuboring' if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True))
    bot.send_message(message.chat.id, "Lakatsiyani jo'nating:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Отправьте ваше местоположение:", reply_markup=markup)
    bot.register_next_step_handler(message, process_location_step)

def process_location_step(message):
    location = f"{message.location.latitude},{message.location.longitude}"
    user_id = message.from_user.id
    user_data[str(user_id)]["location"] = location
    save_user_data(user_data)
    bot.send_message(message.chat.id, "Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Регистрация успешно завершена!", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
    send_main_menu(message)

# Send main menu
def send_main_menu(message):
    language = user_data[str(message.chat.id)]["language"]
    markup = create_main_menu(language)
    bot.send_message(message.chat.id, "Asosiy menyu:" if language == "🇺🇿 O'zbek" else "Главное меню:", reply_markup=markup)

# Mahsulot qo'shish
@bot.message_handler(func=lambda message: message.text == "🆕 Mahsulot qo'shish")
def add_product(message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        bot.send_message(message.chat.id, "Siz admin emassiz.")
        return

    bot.send_message(message.chat.id, "📝 Mahsulot nomini kiriting:")
    bot.register_next_step_handler(message, process_product_name_step)

def process_product_name_step(message):
    user_data[str(message.chat.id)]["product_name"] = message.text
    bot.send_message(message.chat.id, "📸 Mahsulot rasmini yuboring:")
    bot.register_next_step_handler(message, process_product_image_step)

def process_product_image_step(message):
    product_images = [photo.file_id for photo in message.photo]
    user_data[str(message.chat.id)]["product_images"] = product_images
    bot.send_message(message.chat.id, "💰 Mahsulotni birinchi narxini kiriting: (xxx.xxx)")
    bot.register_next_step_handler(message, process_product_first_price_step)

def process_product_first_price_step(message):
    try:
        product_first_price = float(message.text)
        user_data[str(message.chat.id)]["product_first_price"] = product_first_price
        bot.send_message(message.chat.id, "💰 Mahsulotni ikkinchi narxini kiriting: (xxx.xxx) yoki /skip bosing:")
        bot.register_next_step_handler(message, process_product_second_price_step)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Iltimos, to'g'ri narx kiriting.")

def process_product_second_price_step(message):
    if message.text == '/skip':
        product_second_price = None
    else:
        try:
            product_second_price = float(message.text)
            user_data[str(message.chat.id)]["product_second_price"] = product_second_price
        except ValueError:
            bot.send_message(message.chat.id, "❌ Iltimos, to'g'ri narx kiriting yoki /skip bosing.")
            return

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("🥗 Birinchi ovqat"), types.KeyboardButton("🍛 Ikkinchi ovqat"), types.KeyboardButton("🥗 Salat"), types.KeyboardButton("🍱 Setlar"))
    bot.send_message(message.chat.id, "Ovqat turini tanlang:", reply_markup=markup)
    bot.register_next_step_handler(message, process_product_category_step)

def process_product_category_step(message):
    product_category = message.text
    data = user_data[str(message.chat.id)]
    cursor.execute("INSERT INTO products (name, price, net_price, image, category) VALUES (?, ?, ?, ?, ?)",
                   (data['product_name'], data['product_first_price'], data.get('product_second_price'), json.dumps(data.get('product_images')), product_category))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ Mahsulot qo'shildi: {data['product_name']} - {data['product_first_price']} so'm", reply_markup=create_admin_menu())

# Mahsulotni tahrirlash
@bot.message_handler(func=lambda message: message.text == "✏️ Mahsulotni tahrirlash")
def edit_product(message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        bot.send_message(message.chat.id, "Siz admin emassiz.")
        return

    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    if not products:
        bot.send_message(message.chat.id, "Mahsulotlar topilmadi.")
        return

    product_list = "\n".join([f"{product[0]}: {product[1]}" for product in products])
    bot.send_message(message.chat.id, f"Mahsulotlar ro'yxati:\n{product_list}\n\nMahsulot IDsini kiriting:")
    bot.register_next_step_handler(message, process_edit_product_id)

def process_edit_product_id(message):
    product_id = message.text
    if not product_id.isdigit():
        bot.send_message(message.chat.id, "Faqat raqam kiriting.")
        return

    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    if not product:
        bot.send_message(message.chat.id, "Mahsulot topilmadi.")
        return

    user_data[str(message.chat.id)]["edit_product_id"] = product_id
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(types.KeyboardButton("📝 Ismni o'zgartirish"), types.KeyboardButton("💰 Narxni o'zgartirish"))
    bot.send_message(message.chat.id, "Qaysi qismni tahrirlamoqchisiz?", reply_markup=markup)
    bot.register_next_step_handler(message, process_edit_option)

def process_edit_option(message):
    option = message.text
    if option == "📝 Ismni o'zgartirish":
        bot.send_message(message.chat.id, "Yangi nomni kiriting:")
        bot.register_next_step_handler(message, process_edit_product_name)
    elif option == "💰 Narxni o'zgartirish":
        bot.send_message(message.chat.id, "Yangi narxni kiriting: (faqat raqamlar)")
        bot.register_next_step_handler(message, process_edit_product_price)

def process_edit_product_name(message):
    new_name = message.text
    product_id = user_data[str(message.chat.id)]["edit_product_id"]
    cursor.execute("UPDATE products SET name=? WHERE id=?", (new_name, product_id))
    conn.commit()
    bot.send_message(message.chat.id, f"Mahsulot nomi yangilandi: {new_name}", reply_markup=create_admin_menu())

def process_edit_product_price(message):
    try:
        new_price = float(message.text)
        product_id = user_data[str(message.chat.id)]["edit_product_id"]
        cursor.execute("UPDATE products SET price=? WHERE id=?", (new_price, product_id))
        conn.commit()
        bot.send_message(message.chat.id, f"Mahsulot narxi yangilandi: {new_price}", reply_markup=create_admin_menu())
    except ValueError:
        bot.send_message(message.chat.id, "Iltimos, faqat raqam kiriting.")

# Mahsulotni o'chirish
@bot.message_handler(func=lambda message: message.text == "🗑️ Mahsulot o'chirish")
def delete_product(message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        bot.send_message(message.chat.id, "Siz admin emassiz.")
        return

    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    if not products:
        bot.send_message(message.chat.id, "Mahsulotlar topilmadi.")
        return

    product_list = "\n".join([f"{product[0]}: {product[1]}" for product in products])
    bot.send_message(message.chat.id, f"Mahsulotlar ro'yxati:\n{product_list}\n\nO'chiriladigan mahsulot IDsini kiriting:")
    bot.register_next_step_handler(message, process_delete_product_id)

def process_delete_product_id(message):
    product_id = message.text
    if not product_id.isdigit():
        bot.send_message(message.chat.id, "Faqat raqam kiriting.")
        return

    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    if not product:
        bot.send_message(message.chat.id, "Mahsulot topilmadi.")
        return

    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    bot.send_message(message.chat.id, f"Mahsulot o'chirildi: {product[1]}", reply_markup=create_admin_menu())

# Run the bot
bot.infinity_polling()
