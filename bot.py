from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup
from confing import *
from gpt import *
import logging

bot = TeleBot(TOKEN)
MAX_LETTERS = MAX_TOKENS
gpt = GPT()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)

users_history = {} # Словарик для хранения задач пользователей и ответов GPT

# Функция для создания клавиатуры с нужными кнопочками
def create_keyboard(buttons_list):
    keyboard = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    logging.info("Отправка приветственного сообщения")
    bot.send_message(message.chat.id,
                     text=f"Привет, {user_name}! Я бот-мультипомощник и могу помогать по математике, русскому, программированию",
                     reply_markup=create_keyboard(["/solve_task", '/help']))

@bot.message_handler(commands=['help'])
def support(message):
    logging.info("Отправка приветственного сообщения")
    bot.send_message(message.from_user.id,
                     text="Чтобы приступить к решению задачи: нажми /solve_task, а затем напиши условие задачи\n"
                          "а если случилась ошибка, например ответа на вопрос нет не отправилось, то пиши /debug",
                     reply_markup=create_keyboard(["/solve_task"]))

# РЕШЕНИЕ
@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.chat.id, "Напиши условие новой задачи:")
    bot.register_next_step_handler(message, get_promt)
    if not message.text:
        logging.warning("Получено пустое текстовое сообщение")
        bot.reply_to(message, "Пожалуйста, отправь мне какой-нибудь текст.")
        return

def continue_filter(message):
    button_text = 'Продолжить решение'
    return message.text == button_text #Фильтр для обработки кнопочки

# Получение задачи от пользователя или продолжение решения
@bot.message_handler(func=continue_filter)
def get_promt(message):
    user_id = message.from_user.id

    if message.content_type != "text":
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, get_promt)
        return

    user_request = message.text

    if gpt.count_tokens(user_request) > MAX_TOKENS:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, get_promt)
        return

    if (user_id not in users_history or users_history[user_id] == {}) and user_request == "Продолжить решение":
        bot.send_message(user_id, "Чтобы продолжить решение, сначала нужно отправить текст задачи")
        bot.send_message(user_id, "Напиши условие новой задачи:")
        bot.register_next_step_handler(message, get_promt)
        return

    if user_id not in users_history or users_history[user_id] == {}:
        # Сохраняем промт пользователя и начало ответа GPT в словарик users_history
        users_history[user_id] = {
            'system_content': "Ты - дружелюбный помощник для решения задач по математике. Давай подробный ответ с решением на русском языке",
            'user_content': user_request,
            'assistant_content': "Решим задачу по шагам: "
        }

    # GPT: формирование промта и отправка запроса к нейросети
    promt = gpt.make_promt(users_history[user_id])
    resp = gpt.send_request(promt)
    answer = gpt.process_resp(resp)

    users_history[user_id]['assistant_content'] += answer

    # кнопочки "продолжить решение" и "завершить решение"
    bot.send_message(
        user_id,
        text=users_history[user_id]['assistant_content'],
        reply_markup=create_keyboard(["Продолжить решение", "Завершить решение"])
    )

def end_filter(message):
    return message.text == 'Завершить решение'

@bot.message_handler(content_types=['text'], func=end_filter)
def end_task(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "Текущие решение завершено")
    users_history[user_id] = {}
    solve_task(message)
    if (user_id not in users_history or users_history[user_id] == {}) and user_request == "Продолжить решение":
        bot.send_message(user_id, "Чтобы продолжить решение, сначала нужно отправить текст задачи")
        bot.send_message(user_id, "Напиши условие новой задачи:")
        bot.register_next_step_handler(message, get_promt)
        return
 # приветливость
bot.message_handler(content_types=['text'])
def ansvers (message):
    if "прив" in message.text.lower():
        bot.reply_to(message,  text=f"приветики!")
    elif "пока" in message.text.lower():
        bot.reply_to(message,  text=f"пока-пока")
    elif "кто" and "ты" in message.text.lower():
        bot.reply_to(message,  text=f"ты можешь нажать на /about и узнать кто я!")
    elif "как" and "дела" in message.text.lower():
        bot.reply_to(message, text=f"Спасибо, что спросил_а! Дела отлично!")

# снова команды
@bot.message_handler(commands=['help'])
def helper(message):
    bot.reply_to(message, "помощь здесь, что бы задать вопрос нейросети введи /solve_task")

@bot.message_handler(commands=['about'])
def about_command(message):
        bot.send_message(message.from_user.id, text="Рад, что ты заинтересован_а! Мое предназначение — помочь тебе с орыографией в предложениях")

@bot.message_handler(commands=['debug'])
def send_logs(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(func=lambda message: True)
def handle(message):
    prompt = message.txt
    response =  response_gpt(prompt)
    bot.send_message(message.chat.id, response)

bot.polling()
