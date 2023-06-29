import telebot
import userapp
import csv
import passwords


bot = telebot.TeleBot('6197122837:AAE8OGHDbCH3JisyDWwSM6_sr1o2oA1mdno')
current_usersessions = []


error_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
error_markup.add(telebot.types.KeyboardButton("Домой"))
prohibited_passwords = ["Перевести", "/start", "Сменить пароль", "Обновить", "Домой", "Выйти", "help", "/restart", "Попробовать ещё раз"]


def get_usersession(telegram_user_id):
    for itm in current_usersessions:
        if itm.telegram_user_id == telegram_user_id:
            return itm
    return False


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    u = get_usersession(message.from_user.id)
    if not u:
        current_usersessions.append(userapp.UserSession(message.from_user.id))
        u = current_usersessions[-1]
        db_name = "users.db"
        with open(db_name, 'r', newline='', encoding='utf-8') as db_file:
            for line in csv.DictReader(db_file):
                if line["login_automatically"] == "1":
                    if int(line["telegram_user_id"]) == message.from_user.id:
                        print("Попытка автоматического входа...")
                        u.auto_log_in(line["name"], line["id"])
                        bot.send_message(message.from_user.id, f"Добро пожаловать в Наебанк, {line['name']}!", reply_markup=telebot.types.ReplyKeyboardRemove(selective=None))
                        homepage(message)
    if not u.logged_in:
        if message.text in ["/start", "help", "/restart", "Попробовать ещё раз"]:
            bot.send_message(message.from_user.id, "Добро пожаловать в Наебанк! Введите ваш логин", reply_markup=telebot.types.ReplyKeyboardRemove(selective=None))
            bot.register_next_step_handler(message, get_login)
    else:
        if message.text in ["Домой", "Обновить"]:
            homepage(message)


def get_login(message):
    u = get_usersession(message.from_user.id)
    resp = u.try_to_log_in(message.text)
    if resp:
        bot.send_message(message.from_user.id, "Введите пароль")
        bot.register_next_step_handler(message, get_password)
    else:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton("Попробовать ещё раз"))
        bot.send_message(message.from_user.id, "Пользователь с таким именем не найден. Попробуйте снова", reply_markup=markup)
        bot.register_next_step_handler(message, get_text_messages)


def get_password(message):
    u = get_usersession(message.from_user.id)
    resp = u.try_password(message.text)
    if message.text == "/restart":
        get_text_messages(message)
    elif resp:
        bot.send_message(message.from_user.id, f"Добро пожаловать, {resp}!")
        homepage(message)
    else:
        bot.send_message(message.from_user.id, f"Неверный пароль! Введите пароль повторно или введите /restart, чтобы войти в другой аккаунт", reply_markup=None)
        bot.register_next_step_handler(message, get_password)


def homepage(message):
    u = get_usersession(message.from_user.id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("Перевести"))
    markup.add(telebot.types.KeyboardButton("Сменить пароль"))
    markup.add(telebot.types.KeyboardButton("Выйти"))
    bot.send_message(message.from_user.id, u.get_balance(), reply_markup=markup)
    bot.register_next_step_handler(message, action)


def action(message):
    u = get_usersession(message.from_user.id)
    if message.text == "Перевести":
        transfer_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for user in u.bank.users_list:
            if user != u.username:
                transfer_markup.add(telebot.types.KeyboardButton(user))
        bot.send_message(message.from_user.id, "Выберите получателя", reply_markup=transfer_markup)
        bot.register_next_step_handler(message, select_currency)
    elif message.text == "Обновить":
        homepage(message)
    elif message.text == "Сменить пароль":
        bot.send_message(message.from_user.id, "Введите текущий пароль", reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, change_password)
    elif message.text == "Выйти":
        bot.send_message(message.from_user.id, f"До встречи, {u.username}!", reply_markup=telebot.types.ReplyKeyboardRemove())
        u.quit()


def select_currency(message):
    u = get_usersession(message.from_user.id)
    if (message.text in u.bank.users_list) and (message.text != u.username):
        currency_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        u.send_destination = message.text
        for currency in u.bank.acc.currencies_list:
            currency_markup.add(telebot.types.KeyboardButton(currency))
        bot.send_message(message.from_user.id, "Выберите валюту", reply_markup=currency_markup)
        bot.register_next_step_handler(message, select_amount)
    elif message.text == u.username:
        bot.send_message(message.from_user.id, "Нельзя совершить перевод самому себе!", reply_markup=error_markup)
    elif message.text not in u.bank.users_list:
        bot.send_message(message.from_user.id, "Пользователя с указанным именем не существует!", reply_markup=error_markup)


def select_amount(message):
    u = get_usersession(message.from_user.id)
    u.send_currency = message.text
    if message.text in u.bank.acc.currencies_list:
        bot.send_message(message.from_user.id, f"Введите количество {message.text} для отправки (например, 3.14)", reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, send_money_ask)
    else:
        bot.send_message(message.from_user.id, f"Валюты {message.text} не существует!", reply_markup=error_markup)


def send_money_ask(message):
    u = get_usersession(message.from_user.id)
    try:
        amount = float(message.text)
    except ValueError:
        bot.send_message(message.from_user.id, f"Нужно ввести число!", reply_markup=error_markup)
    if amount < 0:
        bot.send_message(message.from_user.id, f"Число не может быть меньше нуля!", reply_markup=error_markup)
    elif amount == 0:
        bot.send_message(message.from_user.id, f"Число не может быть равно нулю!", reply_markup=error_markup)
    else:
        u.send_amount = message.text
        u.transfer()
        bot.send_message(message.from_user.id, f"Перевод выполнен успешно", reply_markup=error_markup)


def change_password(message):
    u = get_usersession(message.from_user.id)
    if u.check_password(message.text):
        bot.send_message(message.from_user.id, f"Введите новый пароль. Пароль должен содержать буквы вернего и нижнего регистра, а также хотя бы одно число, и иметь длину минимум в 8 символов", reply_markup=telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, input_new_password)
    else:
        bot.send_message(message.from_user.id, f"Неверный пароль! Нажмите Домой, чтобы вернуться в главное меню", reply_markup=error_markup)


def input_new_password(message):
    u = get_usersession(message.from_user.id)
    if u.change_password(message.text):
        bot.send_message(message.from_user.id, f"Пароль успешно изменён!", reply_markup=error_markup)
    else:
        bot.send_message(message.from_user.id, f"Пароль не проходит проверку на безопасность. Нажмите Домой, чтобы вернуться в главное меню", reply_markup=error_markup)


bot.polling(none_stop=True, interval=0)
