import json
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from datetime import datetime
import csv

API_TOKEN = "7158602292:AAE9x3Lu-8iRdgi-o8CMfdbxFA649RN4Y5I"
ADMIN_CHAT_IDS = [1593464245]  # Admin chat ID'sini kiriting
ORDER_GROUP_ID = -1002165519452  # Buyurtmalarni yuboradigan guruh ID'sini kiriting

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

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
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    menu_button = KeyboardButton("📜 Menyu" if language == "🇺🇿 O'zbek" else "📜 Меню")
    contact_button = KeyboardButton("☎️ Kontakt" if language == "🇺🇿 O'zbek" else "☎️ Контакт")
    order_button = KeyboardButton("🚖 Buyurtma" if language == "🇺🇿 O'zbek" else "🚖 Заказ")
    cart_button = KeyboardButton("🛒 Savatcha" if language == "🇺🇿 O'zbek" else "🛒 Корзина")
    settings_button = KeyboardButton("⚙️ Sozlamalar" if language == "🇺🇿 O'zbek" else "⚙️ Настройки")
    markup.add(menu_button, contact_button, order_button, cart_button, settings_button)
    return markup

def create_admin_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    send_message_button = KeyboardButton("📢 Habar yuborish")
    add_button = KeyboardButton("🆕 Mahsulot qo'shish")
    edit_button = KeyboardButton("✏️ Mahsulotni tahrirlash")
    delete_button = KeyboardButton("🗑️ Mahsulot o'chirish")
    back_button = KeyboardButton("🔙 Orqaga")
    markup.add(send_message_button, add_button, edit_button, delete_button, back_button)
    return markup

class Registration(StatesGroup):
    language = State()
    name = State()
    phone = State()
    location = State()

class AdminStates(StatesGroup):
    product_name = State()
    product_image = State()
    product_first_price = State()
    product_second_price = State()
    product_category = State()
    edit_product_id = State()
    edit_option = State()
    edit_product_name = State()
    edit_product_price = State()
    delete_product_id = State()

class UserStates(StatesGroup):
    selected_price = State()
    quantity = State()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) in user_data:
        await send_main_menu(message)
    else:
        await start_registration(message)

# Registration 
async def start_registration(message: types.Message):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    uzb_button = KeyboardButton("🇺🇿 O'zbek")
    rus_button = KeyboardButton("🇷🇺 русский")
    markup.add(uzb_button, rus_button)
    await message.answer("Tilni tanlang:", reply_markup=markup)
    await Registration.language.set()

@dp.message_handler(state=Registration.language)
async def process_language_step(message: types.Message, state: FSMContext):
    language = message.text
    if language not in ["🇺🇿 O'zbek", "🇷🇺 русский"]:
        markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add(KeyboardButton("🇺🇿 O'zbek"), KeyboardButton("🇷🇺 русский"))
        await message.answer("Iltimos, tilni tanlang:", reply_markup=markup)
        return
    await state.update_data(language=language)
    await message.answer("Ismingizni kiriting:" if language == "🇺🇿 O'zbek" else "Введите ваше имя:")
    await Registration.next()

@dp.message_handler(state=Registration.name)
async def process_name_step(message: types.Message, state: FSMContext):
    name = message.text
    if not name.isalpha():
        await message.answer("Iltimos, to'g'ri ismingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Пожалуйста, введите правильное имя:")
        return
    await state.update_data(name=name)
    await message.answer("Telefon raqamingizni kiriting: +998XXXXXXXXX" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Введите ваш номер телефона: +998XXXXXXXXX")
    await Registration.next()

@dp.message_handler(state=Registration.phone)
async def process_phone_step(message: types.Message, state: FSMContext):
    phone = message.text
    if not phone.startswith("+998") or not phone[4:].isdigit() or len(phone) != 13:
        await message.answer("Iltimos, to'g'ri telefon raqamini kiriting: +998XXXXXXXXX" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Пожалуйста, введите правильный номер телефона: +998XXXXXXXXX")
        return
    await state.update_data(phone=phone)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton('📍 Lakatsiyani yuboring' if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True))
    await message.answer("Lakatsiyani jo'nating:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Отправьте ваше местоположение:", reply_markup=markup)
    await Registration.next()

@dp.message_handler(state=Registration.location, content_types=types.ContentType.LOCATION)
async def process_location_step(message: types.Message, state: FSMContext):
    location = f"{message.location.latitude},{message.location.longitude}"
    user_id = message.from_user.id
    user_data[str(user_id)] = await state.get_data()
    user_data[str(user_id)]["location"] = location
    save_user_data(user_data)
    await state.finish()
    await message.answer("Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Регистрация успешно завершена!", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
    await send_main_menu(message)

async def send_main_menu(message: types.Message):
    language = user_data[str(message.chat.id)]["language"]
    markup = create_main_menu(language)
    await message.answer("Asosiy menyu:" if language == "🇺🇿 O'zbek" else "Главное меню:", reply_markup=markup)

@dp.message_handler(commands=['admin'])
async def send_admin_menu(message: types.Message):
    if message.chat.id in ADMIN_CHAT_IDS:
        markup = create_admin_menu()
        await message.answer("Admin menyusi" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Админ меню", reply_markup=markup)
    else:
        await message.answer("Siz admin emassiz." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Вы не администратор.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@dp.message_handler(Text(equals="📢 Habar yuborish"))
async def send_message_to_all_users(message: types.Message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        await message.answer("Siz admin emassiz.")
        return

    await message.answer("Iltimos habarni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Введите сообщение:")
    await AdminStates.product_name.set()

@dp.message_handler(state=AdminStates.product_name)
async def process_send_message(message: types.Message, state: FSMContext):
    for user_id in user_data.keys():
        try:
            await bot.send_message(user_id, message.text)
        except:
            continue
    await state.finish()
    await message.answer("Habar yuborildi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Сообщение отправлено.", reply_markup=create_admin_menu())


# Mahsulot qo'shish
@dp.message_handler(Text(equals="🆕 Mahsulot qo'shish"))
async def add_product(message: types.Message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        await message.answer("Siz admin emassiz.")
        return

    await message.answer("📝 Mahsulot nomini kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите название продукта:")
    await AdminStates.product_name.set()

@dp.message_handler(state=AdminStates.product_name)
async def process_product_name_step(message: types.Message, state: FSMContext):
    await state.update_data(product_name=message.text)
    await message.answer("📸 Mahsulot rasmini yuboring:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📸 Отправьте изображение продукта:")
    await AdminStates.next()

@dp.message_handler(state=AdminStates.product_image, content_types=types.ContentType.PHOTO)
async def process_product_image_step(message: types.Message, state: FSMContext):
    product_images = [photo.file_id for photo in message.photo]
    await state.update_data(product_images=product_images)
    await message.answer("💰 Mahsulotni birinchi narxini kiriting: (xxx.xxx)" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите первую цену продукта: (xxx.xxx)")
    await AdminStates.next()

@dp.message_handler(state=AdminStates.product_first_price)
async def process_product_first_price_step(message: types.Message, state: FSMContext):
    try:
        product_first_price = float(message.text)
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri narx kiriting." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, введите правильную цену.", reply_markup=create_admin_menu())
        await state.finish()
        return
    await state.update_data(product_first_price=product_first_price)
    await message.answer("💰 Mahsulotni ikkinchi narxini kiriting: (xxx.xxx) yoki /skip bosing:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "💰 Введите вторую цену продукта: (xxx.xxx) или нажмите /skip:")
    await AdminStates.next()

@dp.message_handler(state=AdminStates.product_second_price)
async def process_product_second_price_step(message: types.Message, state: FSMContext):
    if message.text == '/skip':
        product_second_price = None
    else:
        try:
            product_second_price = float(message.text)
        except ValueError:
            await message.answer("❌ Iltimos, to'g'ri narx kiriting yoki /skip bosing." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, введите правильную цену или нажмите /skip.")
            await state.finish()
            return
    await state.update_data(product_second_price=product_second_price)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("🥗 Birinchi ovqat"), KeyboardButton("🍛 Ikkinchi ovqat"), KeyboardButton("🥗 Salat"), KeyboardButton("🍱 Setlar"))
    markup.add(KeyboardButton("🔙 Orqaga"))
    await message.answer("Ovqat turini tanlang:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Выберите категорию продукта:", reply_markup=markup)
    await AdminStates.next()

@dp.message_handler(state=AdminStates.product_category)
async def process_product_category_step(message: types.Message, state: FSMContext):
    product_category = message.text if message.text != '🔙 Orqaga' else None
    data = await state.get_data()
    cursor.execute("INSERT INTO products (name, price, net_price, image, category) VALUES (?, ?, ?, ?, ?)",
                   (data['product_name'], data['product_first_price'], data.get('product_second_price'), json.dumps(data.get('product_images')), product_category))
    conn.commit()
    second_price_info = f" - {data.get('product_second_price')} so'm" if data.get('product_second_price') else ""
    await state.finish()
    await message.answer(f"✅ Mahsulot qo'shildi: {data['product_name']} - {data['product_first_price']} so'm{second_price_info}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Продукт добавлен: {data['product_name']} - {data['product_first_price']} сум{second_price_info}", reply_markup=create_admin_menu())

@dp.message_handler(lambda message: message.text == "📜 Menyu" or message.text == "📜 Меню")
async def show_menu(message: types.Message):
    language = user_data[str(message.chat.id)]["language"]
    categories = ["🥗 Birinchi ovqat", "🍛 Ikkinchi ovqat", "🥗 Salat", "🍱 Setlar"]

    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for category in categories:
        markup.add(KeyboardButton(category))
    markup.add(KeyboardButton("🏠 Asosiy menyu" if language == "🇺🇿 O'zbek" else "🏠 Главное меню"))

    await message.answer("🍽 Bo'limni tanlang:" if language == "🇺🇿 O'zbek" else "🍽 Выберите категорию:", reply_markup=markup)

@dp.message_handler(lambda message: message.text in ["🥗 Birinchi ovqat", "🍛 Ikkinchi ovqat", "🥗 Salat", "🍱 Setlar"])
async def show_category_items(message: types.Message):
    category = message.text
    cursor.execute("SELECT name FROM products WHERE category = ?", (category,))
    items = cursor.fetchall()

    if not items:
        await message.answer("❌ Bu bo'limda hech narsa yo'q." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ В этой категории пока ничего нет.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for item in items:
        markup.add(KeyboardButton(item[0]))
    markup.add(KeyboardButton("📜 Menyu" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📜 Меню"))

    await message.answer("📋 Mahsulotni tanlang:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📋 Выберите продукт:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == "🏠 Asosiy menyu" or message.text == "🏠 Главное меню")
async def return_to_main_menu(message: types.Message):
    await send_main_menu(message)

# Category List
@dp.message_handler(lambda message: message.text not in ["📜 Menyu", "📜 Меню", "🏠 Asosiy menyu", "🏠 Главное меню", "☎️ Kontakt", "☎️ Контакт", "🚖 Buyurtma", "🚖 Заказ", "🛒 Savatcha", "🛒 Корзина", "⚙️ Sozlamalar", "⚙️ Настройки"])
async def show_product_details(message: types.Message, state: FSMContext):
    product_name = message.text
    cursor.execute("SELECT * FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()
    if not product:
        await message.answer("❌ Bunday mahsulot topilmadi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Продукт не найден.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    await state.update_data(product_id=product[0], quantity=1)
    language = user_data[str(message.chat.id)]["language"]
    caption = f"{product[1]}\n\n{product[2]:,.0f} so'm" if language == "🇺🇿 O'zbek" else f"{product[1]}\n\n{product[2]:,.0f} сум"
    if product[3]:
        caption += f" - {product[3]:,.0f} so'm" if language == "🇺🇿 O'zbek" else f" - {product[3]:,.0f} сум"

    images = json.loads(product[4])
    if images:
        await bot.send_media_group(message.chat.id, [types.InputMediaPhoto(img_id, caption=caption if i == 0 else "") for i, img_id in enumerate(images)])
    else:
        await message.answer(caption)

    await show_price_buttons(message, product[2], product[3])

async def show_price_buttons(message, price, net_price):
    language = user_data[str(message.chat.id)]["language"]
    markup = InlineKeyboardMarkup()
    if net_price:
        markup.add(InlineKeyboardButton(text=f"{price:,} so'm" if language == "🇺🇿 O'zbek" else f"{price:,.0f} сум", callback_data=f"select_price:{price}"),
                   InlineKeyboardButton(text=f"{net_price:,} so'm" if language == "🇺🇿 O'zbek" else f"{net_price:,} сум", callback_data=f"select_net_price:{net_price}"))
    else:
        markup.add(InlineKeyboardButton(text=f"{price:,.0f} so'm" if language == "🇺🇿 O'zbek" else f"{price:,} сум", callback_data=f"select_price:{price}"))
    await message.answer(f"💰 Narxni tanlang:" if language == "🇺🇿 O'zbek" else "💰 Выберите цену:", reply_markup=markup)

@dp.callback_query_handler(lambda call: call.data.startswith("select_price") or call.data.startswith("select_net_price"))
async def callback_select_price(call: types.CallbackQuery, state: FSMContext):
    price = float(call.data.split(":")[1])
    
    # quantity ni boshlang'ich qiymat sifatida 1 qilib o'rnating
    await state.update_data(selected_price=price, quantity=1)
    
    await update_quantity_message(call.message, state)

async def update_quantity_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    language = user_data[str(message.chat.id)]["language"]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="➖", callback_data="decrease"),
               InlineKeyboardButton(text=str(data['quantity']), callback_data="quantity"),
               InlineKeyboardButton(text="➕", callback_data="increase"))
    markup.add(InlineKeyboardButton(text="➕ Qo'shish" if language == "🇺🇿 O'zbek" else "➕ Добавить", callback_data="add_to_cart"),
               InlineKeyboardButton(text="❌ Bekor qilish" if language == "🇺🇿 O'zbek" else "❌ Отмена", callback_data="cancel"))
    await message.answer(f"Nechta buyurtma qilasiz?" if language == "🇺🇿 O'zbek" else f"Сколько хотите заказать?", reply_markup=markup)

@dp.callback_query_handler(lambda call: call.data in ["decrease", "increase", "add_to_cart", "cancel"])
async def callback_inline(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if call.data in ["decrease", "increase"]:
        if call.data == "decrease" and data['quantity'] > 1:
            data['quantity'] -= 1
        elif call.data == "increase":
            data['quantity'] += 1
        await state.update_data(quantity=data['quantity'])
        await call.message.edit_reply_markup(reply_markup=update_quantity_markup(data['quantity'], call.message.chat.id))
    elif call.data == "add_to_cart":
        selected_price = data.get('selected_price', None)
        if selected_price is None:
            await call.answer("Iltimos, narxni tanlang" if user_data[str(call.message.chat.id)]["language"] == "🇺🇿 O'zbek" else "Пожалуйста, выберите цену")
            return
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                       (call.message.chat.id, data['product_id'], data['quantity'], selected_price))
        conn.commit()
        await call.message.edit_text(f"🛒 Savatingizga qo'shildi: {data['quantity']} dona" if user_data[str(call.message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"🛒 Добавлено в корзину: {data['quantity']} шт")
        
        # Mahsulot savatga qo'shilgandan so'ng, yana kategoriyalar bo'limiga qaytish
        await show_menu(call.message)
    elif call.data == "cancel":
        await call.message.edit_text("❌ Bekor qilindi" if user_data[str(call.message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Отменено")
        await show_menu(call.message)

def update_quantity_markup(quantity, chat_id):
    language = user_data[str(chat_id)]["language"]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="➖", callback_data="decrease"),
               InlineKeyboardButton(text=str(quantity), callback_data="quantity"),
               InlineKeyboardButton(text="➕", callback_data="increase"))
    markup.add(InlineKeyboardButton(text="➕ Qo'shish" if language == "🇺🇿 O'zbek" else "➕ Добавить", callback_data="add_to_cart"),
               InlineKeyboardButton(text="❌ Bekor qilish" if language == "🇺🇿 O'zbek" else "❌ Отмена", callback_data="cancel"))
    return markup

@dp.message_handler(lambda message: message.text == "🛒 Savatcha" or message.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        await message.answer("🛒 Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    cart_message = "🛒 Sizning savatingiz:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        cart_message += f"{item[0]} : {item[1]} x {item[2]:,.0f} so'm = {item_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} : {item[1]} x {item[2]:,.0f} сум = {item_price:,.0f} сум\n"
        total_price += item_price
    cart_message += f"💵 Jami: {total_price:,.0f} so'm" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"💵 Итого: {total_price:,.0f} сум"

    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("🚖 Buyurtma qilish" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🚖 Заказ"),
               KeyboardButton("🗑️ Savatchani tozalash" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Очистить корзину"))
    markup.add(KeyboardButton("🏠 Asosiy menyu" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🏠 Главное меню"))

    await message.answer(cart_message, reply_markup=markup)

@dp.message_handler(lambda message: message.text == "🚖 Buyurtma qilish" or message.text == "🚖 Заказ")
async def place_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    if not cart_items:
        await message.answer("🛒 Sizning savatingiz bo'sh." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🛒 Ваша корзина пуста.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    if not is_working_hours():
        await message.answer("🕒 Ish vaqti 09:00dan 23:00gacha" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🕒 Рабочее время с 09:00 до 23:00", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    await message.answer("📞 Telefon raqamingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📞 Введите ваш номер телефона:")
    await UserStates.next()

@dp.message_handler(state=UserStates.selected_price)
async def get_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.text
    await state.update_data(phone_number=phone_number)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton('📍 Lakatsiyani yuboring' if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else '📍 Отправить местоположение', request_location=True))
    await message.answer("📍 Lokatsiyangizni jo'nating:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📍 Отправьте ваше местоположение:", reply_markup=markup)
    await UserStates.next()

@dp.message_handler(state=UserStates.quantity, content_types=types.ContentType.LOCATION)
async def get_location(message: types.Message, state: FSMContext):
    if not message.location:
        await message.answer("❌ Iltimos, lokatsiyani jo'nating." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, отправьте ваше местоположение.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        return

    location = f"{message.location.latitude},{message.location.longitude}"
    user_id = message.from_user.id
    cursor.execute("SELECT products.name, cart.quantity, cart.price FROM cart JOIN products ON cart.product_id = products.id WHERE cart.user_id = ?", (user_id,))
    cart_items = cursor.fetchall()

    order_message = "🆕 Yangi buyurtma:\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🆕 Новый заказ:\n"
    total_price = 0
    for item in cart_items:
        item_price = item[1] * item[2]
        order_message += f"{item[0]} : {item[1]} x {item[2]:,.0f} so'm = {item_price:,.0f} so'm\n" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"{item[0]} : {item[1]} x {item[2]:,.0f} сум = {item_price:,.0f} сум\n"
        total_price += item_price
        cursor.execute("INSERT INTO orders (user_id, product_id, quantity, phone, location) VALUES (?, ?, ?, ?, ?)", (user_id, item[1], item[2], (await state.get_data())['phone_number'], location))
    order_message += f"💵 Jami: {total_price:,.0f} so'm\n📞 Telefon: {(await state.get_data())['phone_number']}\n📍 Lokatsiya: {location}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"💵 Итого: {total_price:,.0f} сум\n📞 Телефон: {(await state.get_data())['phone_number']}\n📍 Местоположение: {location}"
    conn.commit()
    await bot.send_message(ORDER_GROUP_ID, order_message)
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    await message.answer("✅ Buyurtmangiz qabul qilindi! Tez orada operatorlarimiz siz bilan bog'lanadi!" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "✅ Ваш заказ принят! Операторы свяжутся с вами в ближайшее время!", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
    await state.finish()

@dp.message_handler(lambda message: message.text == "🗑️ Savatchani tozalash" or message.text == "🗑️ Очистить корзину")
async def clear_cart(message: types.Message):
    user_id = message.from_user.id
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    await message.answer("🗑️ Savatcha tozalandi." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "🗑️ Корзина очищена.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@dp.message_handler(lambda message: message.text == "☎️ Kontakt" or message.text == "☎️ Контакт")
async def show_contact(message: types.Message):
    await message.answer("📞 Murojaat uchun: +998 99 640 33 37\n@roziboyevdev" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📞 Контакты: +998 99 640 33 37\n@roziboyevdev", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@dp.message_handler(lambda message: message.text == "⚙️ Sozlamalar" or message.text == "⚙️ Настройки")
async def show_settings(message: types.Message):
    language = user_data[str(message.chat.id)]["language"]
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    edit_name_button = KeyboardButton("📝 Ismni o'zgartirish" if language == "🇺🇿 O'zbek" else "📝 Изменить имя")
    change_language_button = KeyboardButton("🌐 Tilni o'zgartirish" if language == "🇺🇿 O'zbek" else "🌐 Изменить язык")
    back_button = KeyboardButton("🏠 Asosiy menyu" if language == "🇺🇿 O'zbek" else "🏠 Главное меню")
    markup.add(edit_name_button, change_language_button, back_button)
    await message.answer("⚙️ Sozlamalar:" if language == "🇺🇿 O'zbek" else "⚙️ Настройки:", reply_markup=markup)

@dp.message_handler(lambda message: message.text == "📝 Ismni o'zgartirish" or message.text == "📝 Изменить имя")
async def change_name(message: types.Message):
    await message.answer("📝 Yangi ismingizni kiriting:" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "📝 Введите ваше новое имя:")
    await Registration.name.set()

@dp.message_handler(state=Registration.name)
async def update_name(message: types.Message, state: FSMContext):
    new_name = message.text
    user_id = message.from_user.id
    user_data[str(user_id)]["name"] = new_name
    save_user_data(user_data)
    await state.finish()
    await message.answer(f"✅ Ismingiz o'zgartirildi: {new_name}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Ваше имя изменено: {new_name}", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))

@dp.message_handler(lambda message: message.text == "🌐 Tilni o'zgartirish" or message.text == "🌐 Изменить язык")
async def change_language(message: types.Message):
    language = user_data[str(message.chat.id)]["language"]
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    uzb_button = KeyboardButton("🇺🇿 O'zbek")
    rus_button = KeyboardButton("🇷🇺 русский")
    markup.add(uzb_button, rus_button)
    await message.answer("🌐 Tilni tanlang:" if language == "🇺🇿 O'zbek" else "🌐 Выберите язык:", reply_markup=markup)
    await Registration.language.set()

@dp.message_handler(state=Registration.language)
async def update_language(message: types.Message, state: FSMContext):
    new_language = message.text
    if new_language not in ["🇺🇿 O'zbek", "🇷🇺 русский"]:
        await message.answer("❌ Iltimos, tilni tanlang." if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else "❌ Пожалуйста, выберите язык.", reply_markup=create_main_menu(user_data[str(message.chat.id)]["language"]))
        await state.finish()
        return
    user_id = message.from_user.id
    user_data[str(user_id)]["language"] = new_language
    save_user_data(user_data)
    await state.finish()
    await message.answer(f"✅ Til o'zgartirildi: {new_language}" if user_data[str(message.chat.id)]["language"] == "🇺🇿 O'zbek" else f"✅ Язык изменен: {new_language}", reply_markup=create_main_menu(new_language))

# Admin Menu Handlers
@dp.message_handler(Text(equals="✏️ Mahsulotni tahrirlash"))
async def edit_product(message: types.Message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        await message.answer("Siz admin emassiz.")
        return

    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    if not products:
        await message.answer("Mahsulotlar topilmadi.")
        return

    product_list = "\n".join([f"{product[0]}: {product[1]}" for product in products])
    await message.answer(f"Mahsulotlar ro'yxati:\n{product_list}\n\nMahsulot IDsini kiriting:")
    await AdminStates.edit_product_id.set()

@dp.message_handler(state=AdminStates.edit_product_id)
async def process_edit_product_id(message: types.Message, state: FSMContext):
    product_id = message.text
    if not product_id.isdigit():
        await message.answer("Faqat raqam kiriting.")
        return

    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    if not product:
        await message.answer("Mahsulot topilmadi.")
        return

    await state.update_data(product_id=product_id)
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(KeyboardButton("📝 Ismni o'zgartirish"), KeyboardButton("💰 Narxni o'zgartirish"))
    markup.add(KeyboardButton("🔙 Orqaga"))
    await message.answer("Qaysi qismni tahrirlamoqchisiz?", reply_markup=markup)
    await AdminStates.edit_option.set()

@dp.message_handler(state=AdminStates.edit_option)
async def process_edit_option(message: types.Message, state: FSMContext):
    option = message.text
    if option == "📝 Ismni o'zgartirish":
        await message.answer("Yangi nomni kiriting:")
        await AdminStates.edit_product_name.set()
    elif option == "💰 Narxni o'zgartirish":
        await message.answer("Yangi narxni kiriting: (faqat raqamlar)")
        await AdminStates.edit_product_price.set()
    else:
        await state.finish()
        await send_admin_menu(message)

@dp.message_handler(state=AdminStates.edit_product_name)
async def process_edit_product_name(message: types.Message, state: FSMContext):
    new_name = message.text
    data = await state.get_data()
    product_id = data.get("product_id")

    cursor.execute("UPDATE products SET name=? WHERE id=?", (new_name, product_id))
    conn.commit()
    await state.finish()
    await message.answer(f"Mahsulot nomi yangilandi: {new_name}")
    await send_admin_menu(message)

@dp.message_handler(state=AdminStates.edit_product_price)
async def process_edit_product_price(message: types.Message, state: FSMContext):
    try:
        new_price = float(message.text)
    except ValueError:
        await message.answer("Iltimos, faqat raqam kiriting.")
        return

    data = await state.get_data()
    product_id = data.get("product_id")

    cursor.execute("UPDATE products SET price=? WHERE id=?", (new_price, product_id))
    conn.commit()
    await state.finish()
    await message.answer(f"Mahsulot narxi yangilandi: {new_price}")
    await send_admin_menu(message)


@dp.message_handler(state=AdminStates.delete_product_id)
async def process_delete_product_id(message: types.Message, state: FSMContext):
    product_id = message.text
    if not product_id.isdigit():
        await message.answer("Faqat raqam kiriting.")
        return

    cursor.execute("SELECT * FROM products WHERE id=?", (product_id,))
    product = cursor.fetchone()
    if not product:
        await message.answer("Mahsulot topilmadi.")
        return

    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    await state.finish()
    await message.answer(f"Mahsulot o'chirildi: {product[1]}")
    await send_admin_menu(message)

@dp.message_handler(Text(equals="📋 Foydalanuvchilar ro'yxati"))
async def export_user_list(message: types.Message):
    if message.chat.id not in ADMIN_CHAT_IDS:
        await message.answer("Siz admin emassiz.")
        return

    with open('user_list.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Ism', 'Telefon', 'Lokatsiya'])
        for user_id, info in user_data.items():
            writer.writerow([user_id, info['name'], info['phone'], info['location']])

    await message.answer_document(open('user_list.csv', 'rb'))
    await send_admin_menu(message)

@dp.message_handler(Text(equals="🔙 Orqaga"))
async def back_to_admin_menu(message: types.Message, state: FSMContext):
    await state.finish()
    await send_admin_menu(message)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
