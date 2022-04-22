from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from bot_app.models import Game, Profile

import telebot
from telebot import types

bot = telebot.TeleBot(token=settings.API_TOKEN)


def main_keyboard(username):
    """Кнопки для основного меню"""
    obj = Profile.objects.get(username=username)
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Ваш профиль', callback_data="Profile")
    btn2 = types.InlineKeyboardButton(text='Редактировать профиль', callback_data="Edit")
    btn3 = types.InlineKeyboardButton(text='Поиск', callback_data="Search")
    if obj.active:
        btn4 = types.InlineKeyboardButton(text="Убрать из поиска", callback_data="inactive")
    else:
        btn4 = types.InlineKeyboardButton(text="Вернуть меня в поиск", callback_data="active")
    keyboard.add(btn1, btn2, btn3, btn4)
    return keyboard


def search_profile_btn(favorite_chat_id, username):
    """Кнопки для поиска пользователей и отправки сообщений"""
    obj = Profile.objects.get(username=username)
    obj.choice = favorite_chat_id
    obj.save()
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton(text='Поиграем?', callback_data="send_message")
    btn2 = types.InlineKeyboardButton(text='Следующая карточка', callback_data="next_profile")
    keyboard.add(btn1, btn2)
    return keyboard


@bot.message_handler(commands=["start"])
def start_command(message):
    """Запуск бота командой /start"""
    # Проверка на наличия в телегаме username
    if message.from_user.username == None:
        bot.send_message(message.chat.id, text="В телеграме не указан username, укажите его в настройках и "
                                               "скорее возвращайтесь!")
    else:
        first_name = message.from_user.first_name
        try:
            # Если профиль создан, приветствуем пользователя
            obj = Profile.objects.get(username=message.from_user.username)
            bot.send_message(message.chat.id,
                             text=f'Добро пожаловать, {first_name}!',
                             reply_markup=main_keyboard(message.from_user.username)
                             )
        except:
            # Первичное заполнение профиля
            obj = Profile(username=message.from_user.username, chat_id=message.chat.id)
            obj.save()
            reply_text = f"Здравствуй, {first_name}! Я занимаюсь поиском тимейтов исходя из " \
                         f"твоих предпочтений. Чтобы начать необходимо заполнить профиль, приступим?"
            keyboard = types.InlineKeyboardMarkup()
            # Согласие на заполнение карточки профиля
            keyboard_1 = types.InlineKeyboardButton(text='Да', callback_data="Yes")
            keyboard_2 = types.InlineKeyboardButton(text='Нет', callback_data='No')
            keyboard.add(keyboard_1, keyboard_2)
            bot.send_message(message.chat.id, text=reply_text, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def inline_callback_btn(call):
    """Обработчик кнопок"""
    obj = Profile.objects.get(username=call.from_user.username)
    # Согласие на заполнение профиля
    if call.data == "Yes":
        send_login(call.message)
    # Отказ о заполнении данных профиля
    elif call.data == "No":
        # Удаляем первично заполненные данные
        bot.edit_message_text(chat_id=obj.chat_id,
                              message_id=call.message.message_id,
                              text="Вызовите команду /start, как будете готовы, мы будем ждать!")
        obj.delete()
    # Редактирование профиля
    elif call.data == "Edit":
        send_login(call.message)
    # Убрать из поиска
    elif call.data == "inactive":
        obj.active = False
        obj.save()
        bot.edit_message_text(chat_id=obj.chat_id,
                              message_id=call.message.message_id,
                              text="Мы убрали Вас из поиска!",
                              reply_markup=main_keyboard(obj.username))
    # Вернуть в поиск
    elif call.data == "active":
        obj.active = True
        obj.save()
        bot.edit_message_text(chat_id=obj.chat_id,
                              message_id=call.message.message_id,
                              text="Мы вернули Вас в поиск!",
                              reply_markup=main_keyboard(obj.username))
    # Информация о профиле пользователя
    elif call.data == "Profile":
        bot.edit_message_text(chat_id=obj.chat_id,
                              message_id=call.message.message_id,
                              text=f"*Профиль стим:* {obj.steam}\n"
                                   f"*О себе:* {obj.about}\n"
                                   f"*Игра:* {obj.game}\n",
                              reply_markup=main_keyboard(obj.username), parse_mode="Markdown")
    # Поиск
    elif call.data == "Search":
        obj.step = 0
        obj.save()
        search_profile(call.from_user.username, obj.step, call.message.message_id)
    # Следующий профиль
    elif call.data == "next_profile":
        obj.step = obj.step + 1
        obj.save()
        search_profile(call.from_user.username, obj.step, call.message.message_id)
    # Отправка сообщения пользователю
    elif call.data == "send_message":
        favorite_chat_id = obj.choice
        bot.send_message(chat_id=favorite_chat_id,
                         text=f"Пользователю @{call.from_user.username} понравилась ваша карточка, напиши ему!")
        bot.send_message(chat_id=obj.chat_id,
                         text='Ваше сообщение успешно отправлено!')


def send_login(message):
    """Получение логина в стим"""
    # Удаление предыдущих кнопок
    markup = types.ReplyKeyboardRemove(selective=False)
    msg = bot.send_message(message.chat.id, "Введите свой логин в стиме", reply_markup=markup)
    # Ожидание ответа и переход на следующую функцию
    bot.register_next_step_handler(msg, send_about)


def send_about(message):
    """Получение рассказа о себе"""
    obj = Profile.objects.get(username=message.from_user.username)
    # Запись логина в стим
    obj.steam = message.text
    obj.save()
    msg = bot.send_message(message.chat.id, "Расскажите немного о себе!")
    # Ожидание ответа и переход на следующую функцию
    bot.register_next_step_handler(msg, send_game)


def send_game(message):
    """Выбор игры"""
    # Запись информации о себе
    obj = Profile.objects.get(username=message.from_user.username)
    obj.about = message.text
    obj.save()
    # Получение списка игр из базы данных в виде ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True, row_width=2)
    queryset = Game.objects.all()
    for id, q in enumerate(queryset):
        id = types.KeyboardButton(f'{q.name}')
        markup.add(id)
    msg = bot.send_message(message.from_user.id, "Выберите игру из предложенных", reply_markup=markup)
    # Ожидание ответа и переход на следующую функцию
    bot.register_next_step_handler(msg, last_process)


def last_process(message):
    """Информация о успешной регистрации"""
    try:
        # Запись выбранной игры пользователем
        first_name = message.from_user.first_name
        obj = Profile.objects.get(username=message.from_user.username)
        obj.game = message.text
        obj.save()
        # Информация об успешной регистрации
        bot.send_message(message.chat.id, 'Профиль успешно заполнен', reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id,
                         text=f'Добро пожаловать, {first_name}!',
                         reply_markup=main_keyboard(message.from_user.username)
                         )
    except Exception as e:
        bot.reply_to(message, "Вы уже зарегистрированы.")


def search_profile(username, count, message_id):
    """Осуществляется поиск пользователей"""
    # Получаем игру по которой будем искать пользователя
    obj = Profile.objects.get(username=username)
    game = obj.game
    profiles = Profile.objects.filter(active=True, game=game)
    # В случае если игрок находится в поиске данной игры один
    if len(profiles) == 1:
        bot.edit_message_text(chat_id=obj.chat_id,
                              message_id=message_id,
                              text="Кажется Вы пока один, не расстраивайтесь, думаю скоро будет много желающих сыграть"
                                   " в эту игру!",
                              reply_markup=main_keyboard(username))
    # Иначе
    else:
        # Ищем пользователей у которых активный статус и совпадают игры
        # Фильтруем все профили
        profiles = profiles.filter(~Q(username=username), active=True, game=game)[count:count + 1]
        # В случае если список игроков пуст
        if int(len(profiles)) == 0:
            bot.edit_message_text(chat_id=obj.chat_id,
                                  message_id=message_id,
                                  text="На данный момент активных игроков c выбранной Вами игрой больше нет!",
                                  reply_markup=main_keyboard(username))

        for profile in profiles:
            # Чат пользователя, чья карточка нам понравилась
            favorite_chat_id = profile.chat_id
            # Отправляем пользователю карточки игроков
            bot.edit_message_text(chat_id=obj.chat_id,
                                  message_id=message_id,
                                  text=f"Карточка игрока\n"
                                       f"Профиль стим: {profile.steam}\n"
                                       f"Любимая игра: {profile.game}\n"
                                       f"Информация об игроке: {profile.about}",
                                  reply_markup=search_profile_btn(favorite_chat_id, username))


# Регистрация команды в manage.py
class Command(BaseCommand):
    help = 'Телеграм-бот'

    def handle(self, *args, **options):
        print(bot.get_me())
        print("Чтобы завершить работу бота нажмите сочетания клавиш CTR+C")
        bot.polling(none_stop=True, interval=0)
