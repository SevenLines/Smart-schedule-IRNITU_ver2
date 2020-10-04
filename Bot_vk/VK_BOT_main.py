import types

from vk_api import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from functions.creating_schedule import full_schedule_in_str, get_one_day_schedule_in_str
from functions.find_week import find_week
from functions.near_lesson import get_near_lesson
from vkbottle.bot import Bot, Message
from functions.storage import MongodbService
from vkbottle.keyboard import Keyboard, Text
from vkbottle.api.keyboard import keyboard_gen
from vkbottle.ext import Middleware
import vk
import json
import typing
from aiohttp import web
import os

token = os.environ.get('VK')
authorize = vk_api.VkApi(token=token)
longpoll = VkLongPoll(authorize)

MAX_CALLBACK_RANGE = 41
storage = MongodbService().get_instance()
bot = Bot(f"{os.environ.get('VK')}", debug="DEBUG")  # TOKEN

content_types = {'text': ['Расписание', 'Ближайшая пара', 'Расписание на сегодня', 'Назад']}
content_notification = {'text': ['Напоминание', 'Настройки', '<==Назад']}


def parametres_for_buttons_start_menu_vk(text, color):
    '''Возвращает параметры кнопок'''
    return {
        "action": {
            "type": "text",
            "payload": "{\"button\": \"" + "1" + "\"}",
            "label": f"{text}"
        },
        "color": f"{color}"
    }


def get_notifications_status(time):
    """Статус напоминаний"""
    if not time or time == 0:
        notifications_status = 'Напоминания выключены ❌\n' \
                               'Воспользуйтесь настройками, чтобы включить'
    else:
        notifications_status = f'Напоминания включены ✅\n' \
                               f'Сообщение придёт за {time} мин до начала пары 😇'
    return notifications_status


def make_inline_keyboard_notifications():
    """Кнопка 'Настройка уведомлений'"""
    keyboard = Keyboard(one_time=False)
    keyboard.add_row()
    keyboard.add_button(Text(label='Настройки'), color="primary")
    keyboard.add_row()
    keyboard.add_button(Text(label='<==Назад'), color="primary")
    return keyboard


def make_keyboard_start_menu():
    """Создаём основные кнопки"""
    keyboard = Keyboard(one_time=False)
    keyboard.add_row()
    keyboard.add_button(Text(label="Расписание"), color="primary")
    keyboard.add_button(Text(label="Ближайшая пара"), color="primary")
    keyboard.add_row()
    keyboard.add_button(Text(label="Расписание на сегодня"), color="default")
    keyboard.add_button(Text(label="Напоминание"), color="default")
    return keyboard


def make_keyboard_institutes(institutes=[]):
    """Кнопки выбора института"""
    keyboard = {
        "one_time": False
    }
    list_keyboard_main = []
    for institute in institutes:
        if len(institute['name']) >= MAX_CALLBACK_RANGE:
            name = sep_space(institute['name'])
        else:
            name = institute['name']
        list_keyboard = []
        list_keyboard.append(parametres_for_buttons_start_menu_vk(f'{name}', 'primary'))
        list_keyboard_main.append(list_keyboard)
    keyboard['buttons'] = list_keyboard_main
    keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
    keyboard = str(keyboard.decode('utf-8'))
    return keyboard


def make_keyboard_choose_course_vk(courses):
    '''Создаёт клавиатуру для выбора курса'''
    keyboard = {
        "one_time": False
    }
    list_keyboard_main = []
    for course in courses:
        name = course['name']
        list_keyboard = []
        list_keyboard.append(parametres_for_buttons_start_menu_vk(f'{name}', 'primary'))
        list_keyboard_main.append(list_keyboard)
    keyboard['buttons'] = list_keyboard_main
    keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
    keyboard = str(keyboard.decode('utf-8'))
    return keyboard


def make_keyboard_choose_group_vk(groups=[]):
    """Кнопки выбора института"""
    keyboard = {
        "one_time": False
    }
    list_keyboard_main_2 = []
    list_keyboard_main = []
    list_keyboard = []
    overflow = 0
    for group in groups:
        overflow += 1
        if overflow == 27:
            list_keyboard_main.append(list_keyboard)
            list_keyboard = []
            list_keyboard.append(parametres_for_buttons_start_menu_vk('Далее', 'primary'))
            list_keyboard_main.append(list_keyboard)
        else:
            if overflow < 28:
                if len(list_keyboard) == 3:
                    list_keyboard_main.append(list_keyboard)
                    list_keyboard = []
                    list_keyboard.append(parametres_for_buttons_start_menu_vk(f'{group}', 'primary'))
                else:
                    list_keyboard.append(parametres_for_buttons_start_menu_vk(f'{group}', 'primary'))
            else:
                list_keyboard = []
                list_keyboard.append(parametres_for_buttons_start_menu_vk(f'{group}', 'primary'))
                list_keyboard_main_2.append(parametres_for_buttons_start_menu_vk(f'{group}', 'primary'))

    if overflow < 28:
        list_keyboard_main.append(list_keyboard)
    else:
        list_keyboard_main_2.append(list_keyboard)

    keyboard['buttons'] = list_keyboard_main
    keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
    keyboard = str(keyboard.decode('utf-8'))

    return keyboard


def make_keyboard_choose_schedule():
    keyboard = Keyboard(one_time=False)
    keyboard.add_row()
    keyboard.add_button(Text(label="На текущую неделю"), color="primary")
    keyboard.add_button(Text(label="На следующую неделю"), color="primary")
    keyboard.add_row()
    keyboard.add_button(Text(label="Основное меню"), color="default")
    return keyboard


def make_keyboard_choose_group_vk_page_2(groups=[]):
    '''Создаёт клавиатуру для групп после переполнения первой'''
    keyboard = {
        "one_time": False
    }
    groups = groups[26:]
    list_keyboard_main = []
    list_keyboard = []
    for group in groups:
        if len(list_keyboard) == 3:
            list_keyboard_main.append(list_keyboard)
            list_keyboard = []
        else:
            list_keyboard.append(parametres_for_buttons_start_menu_vk(f'{group}', 'primary'))
    list_keyboard_main.append(list_keyboard)
    list_keyboard_main.append([parametres_for_buttons_start_menu_vk('Назад', 'primary')])

    keyboard['buttons'] = list_keyboard_main
    keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
    keyboard = str(keyboard.decode('utf-8'))
    return keyboard


def sep_space(name):
    '''Обрезает длину института, если тот больше 40 символов'''
    dlina = abs(len(name) - MAX_CALLBACK_RANGE)
    name = name[:len(name) - dlina - 5]
    return name


def name_institutes(institutes=[]):
    '''Храним список всех институтов'''
    list_institutes = []
    for i in institutes:
        name = i['name']
        list_institutes.append(name)
    return list_institutes


def name_courses(courses=[]):
    '''Храним список всех институтов'''
    list_courses = []
    for i in courses:
        name = i['name']
        list_courses.append(name)
    return list_courses


def name_groups(groups=[]):
    '''Храним список всех групп'''
    list_groups = []
    for i in groups:
        name = i['name']
        list_groups.append(name)
    return list_groups


def listening():
    '''Ждёт сообщение'''
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                message = event.text
                return message

def data_number_wait():
    while True:
        data = listening()
        if data.isdigit():
            return data
        elif '<==Назад' in data:
            return data
        else:
            return 0



@bot.on.message(text='/start')
async def start(ans: Message):
    '''Начало регистрации'''
    chat_id = ans.from_id
    # Проверяем есть пользователь в базе данных
    if storage.get_user(chat_id):
        storage.delete_user_or_userdata(chat_id)  # Удаляем пользвателя из базы данных
    await ans('Привет\n')
    await ans('Для начала пройдите небольшую регистрацию😉\n')
    await ans('Выберите институт.', keyboard=make_keyboard_institutes(storage.get_institutes()))


@bot.on.message(text=content_types['text'])
async def scheduler(ans: Message):
    chat_id = ans.from_id
    data = ans.text
    user = storage.get_user(chat_id=chat_id)
    # listening()

    if 'Расписание' == data and user:
        await ans('Выберите период\n', keyboard=make_keyboard_choose_schedule())
        data = listening()

    if ('На текущую неделю' == data or 'На следующую неделю' == data) and user:
        group = storage.get_user(chat_id=chat_id)['group']
        schedule = storage.get_schedule(group=group)
        if not schedule:
            await ans('Расписание временно недоступно\nПопробуйте позже⏱')
            return

        schedule = schedule['schedule']
        week = find_week()

        # меняем неделю
        if data == 'На следующую неделю':
            week = 'odd' if week == 'even' else 'even'

        week_name = 'четная' if week == 'odd' else 'нечетная'

        schedule_str = full_schedule_in_str(schedule, week=week)
        await ans(f'Расписание {group}\n'
                  f'Неделя: {week_name}', keyboard=make_keyboard_start_menu())

        for schedule in schedule_str:
            await ans(f'{schedule}')

    elif 'Расписание на сегодня' == data and user:
        group = storage.get_user(chat_id=chat_id)['group']
        schedule = storage.get_schedule(group=group)
        if not schedule:
            await ans('Расписание временно недоступно🚫😣\n'
                      'Попробуйте позже⏱', keyboard=make_keyboard_start_menu())
            return
        schedule = schedule['schedule']
        week = find_week()
        schedule_one_day = get_one_day_schedule_in_str(schedule=schedule, week=week)
        await ans(f'{schedule_one_day}')

    elif 'Ближайшая пара' in data and user:
        group = storage.get_user(chat_id=chat_id)['group']
        schedule = storage.get_schedule(group=group)
        if not schedule:
            await ans('Расписание временно недоступно🚫😣\n'
                      'Попробуйте позже⏱')
            return
        schedule = schedule['schedule']
        week = find_week()
        near_lessons = get_near_lesson(schedule=schedule, week=week)

        # если пар нет
        if not near_lessons:
            await ans('Сегодня больше пар нет 😎')
            return

        near_lessons_str = ''
        for near_lesson in near_lessons:
            name = near_lesson['name']
            if name == 'свободно':
                await ans('Сегодня больше пар нет 😎')
                return
            near_lessons_str += '-------------------------------------------\n'
            aud = near_lesson['aud']
            if aud:
                aud = f'Аудитория: {aud}\n'
            time = near_lesson['time']
            info = near_lesson['info']
            prep = near_lesson['prep']

            near_lessons_str += f'{time}\n' \
                                f'{aud}' \
                                f'{name}\n' \
                                f'{info} {prep}\n'
        near_lessons_str += '-------------------------------------------\n'
        await ans(f'Ближайшая пара\n'f'{near_lessons_str}')

@bot.on.message(text=content_notification['text'])
async def scheduler(ans: Message):
    chat_id = ans.from_id
    data = ans.text
    user = storage.get_user(chat_id=chat_id)

    if 'Напоминание' in data and user:
        time = user['notifications']
        if time:
            await ans('У вас уже установлено напоминание: ' + f'{time}' + ' минут',
                      keyboard=make_inline_keyboard_notifications())
        else:
            await ans('У вас не установлено напоминание ', keyboard=make_inline_keyboard_notifications())
        return

    # elif 'Настройки' in data and user:
    #     await ans('Укажите за сколько минут до начала пары должно приходить сообщение [кратное 5]')
    #     data = listening()
    #     while data.isdigit() or ('<==Назад' in data):
    #         await ans('Укажите за сколько минут до начала пары должно приходить сообщение [кратное 5]')
    # 
    #         if '<==Назад' in data:
    #             await ans('Можете посмотреть расписание', keyboard=make_keyboard_start_menu())
    #             return
    #         elif data.isdigit():
    #             if int(data)%5==0:
    #                 time = int(data)
    #                 storage.save_or_update_user(chat_id=chat_id, notifications=time)
    #                 await ans('Вы успешно устновили напоминание: ' + f'{time}' + ' минут', keyboard=make_keyboard_start_menu())
    #                 return
    #             else:
    #                 await ans('Вы указали число не [кратное 5]')






    elif '<==Назад' in data and user:
        await ans('Можете посмотреть расписание', keyboard=make_keyboard_start_menu())

    else:
        await ans('Я вас не понимаю!')



    # elif 'Подтвердить' in data:
    #     data = json.loads(data)
    #     time = data['save_notifications']
    #
    #     group = storage.get_user(chat_id=chat_id)['group']
    #
    #     schedule = storage.get_schedule(group=group)['schedule']
    #     if time > 0:
    #         reminders = calculating_reminder_times(schedule=schedule, time=int(time))
    #     else:
    #         reminders = []
    #     pprint(reminders)
    #     storage.save_or_update_user(chat_id=chat_id, notifications=time, reminders=reminders)

    # elif 'Основное меню' in data and user:
    #     bot.send_message(chat_id, text='Основное меню', reply_markup=make_keyboard_start_menu())
    #
    # else:
    #     bot.send_message(chat_id, text='Я вас не понимаю 😞')


@bot.on.message()
async def wrapper(ans: Message):
    '''Регистрация пользователя'''
    chat_id = ans.from_id
    message = ans.text
    user = storage.get_user(chat_id)
    # Если пользователя нет в базе данных
    if not user:
        institutes = name_institutes(storage.get_institutes())
        # Смотрим выбрал ли пользователь институт
        if message in institutes:
            # Если да, то записываем в бд
            storage.save_or_update_user(chat_id=chat_id, institute=message)
            await ans('Найс\n')
            await ans('Выберите курс.', keyboard=make_keyboard_choose_course_vk(storage.get_courses(message)))
        else:
            await ans('Я вас не понимаю\n')
        return
    # Регистрация после выбора института
    elif not 'course' in user.keys():
        institute = user['institute']
        course = storage.get_courses(institute)
        # Если нажал кнопку курса
        if message in name_courses(course):
            # Записываем в базу данных выбранный курс
            storage.save_or_update_user(chat_id=chat_id, course=message)
            groups = storage.get_groups(institute=institute, course=message)
            groups = name_groups(groups)
            await ans('Выберите группу.', keyboard=make_keyboard_choose_group_vk(groups))
            await ans('Найс2\n')
        else:
            await ans('Я вас не понимаю\n')
        return
    # Регистрация после выбора курса
    elif not 'group' in user.keys():
        institute = user['institute']
        course = user['course']
        groups = storage.get_groups(institute=institute, course=course)
        groups = name_groups(groups)
        # Если нажал кнопку группы
        if message in groups:
            # Записываем в базу данных выбранную группу
            storage.save_or_update_user(chat_id=chat_id, group=message)
            await ans('Конграт.', keyboard=make_keyboard_start_menu())
        else:
            if message == "Далее":
                await ans('Выберите группу.', keyboard=make_keyboard_choose_group_vk_page_2(groups))
            elif message == "Назад":
                await ans('Выберите группу.', keyboard=make_keyboard_choose_group_vk(groups))
            else:
                await ans('Я вас не понимаю\n')
        return


def main():
    '''Запуск бота'''
    bot.run_polling()


if __name__ == "__main__":
    main()
