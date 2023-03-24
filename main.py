import telebot
from telebot import types
from config import TOKEN, DATA_TICKER
from extensions import Converter, APIException

bot = telebot.TeleBot(TOKEN)

# я не нашел в документации сохраняются ли куда-нибудь CallbackQuery запросы, чтобы
# узнать количество, поэтому сохраняю в список

data_query = []
data_curr = []


def commands_markup():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons_list = ['/convert', '/values', '/help']
    buttons = []
    for i in buttons_list:
        buttons.append(types.InlineKeyboardButton(text=i, callback_data=i))
    markup.add(*buttons)
    return markup


def create_markup(hid=None):
    markup = types.InlineKeyboardMarkup()
    buttons = []
    for i in DATA_TICKER:
        if i != hid:
            buttons.append(types.InlineKeyboardButton(text=i, callback_data=i))
    markup.add(*buttons)
    return markup


def clear_data():
    data_curr.clear()
    data_query.clear()


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "/help":
        handle_start_help(call.message)
    elif call.data == "/values":
        handle_values(call.message)
    elif call.data == "/convert":
        handle_convert(call.message)
    elif call.data in DATA_TICKER:
        data_query.append(call.data)
        if len(data_query) >= 2:
            to_handler(call.message, call.data)
        else:
            from_handler(call.message, call.data)
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['start', 'help', ])
def handle_start_help(message: telebot.types.Message):
    clear_data()
    text = 'Бот производит конвертацию из одной валюты в другую.\n\nСписок доступных для конвертации валют: /values\n\
Для конвертации, воспользуйтесь командой /convert или напишите боту в следующем формате:\n\n<ИМЯ ПЕРЕВОДИМОЙ ВАЛЮТЫ> \
<В КАКУЮ ВАЛЮТУ ПЕРЕВЕСТИ> <КОЛИЧЕСТВО ПЕРЕВОДИМОЙ ВАЛЮТЫ>\n\nДоступные команды:\n/convert - конвертация.\n/values - \
список доступных валют.\n/help - помощь.'
    bot.send_message(message.chat.id, text, reply_markup=commands_markup())


@bot.message_handler(commands=['values'])
def handle_values(message: telebot.types.Message):
    clear_data()
    text = 'Доступные валюты:\n'
    for i in DATA_TICKER:
        text += '\n' + i
    bot.send_message(message.chat.id, text, reply_markup=commands_markup())


@bot.message_handler(commands=['convert'])
def handle_convert(message: telebot.types.Message):
    clear_data()
    text = 'Выберете валюту из которой конвертировать:'
    bot.send_message(message.chat.id, text, reply_markup=create_markup())


def from_handler(message: telebot.types.Message, base):
    text = 'Выберете валюту в которую конвертировать:'
    bot.send_message(message.chat.id, text, reply_markup=create_markup(hid=base))
    data_curr.append(base)


def to_handler(message: telebot.types.Message, quote):
    text = 'Напишите количество конвертируемой валюты:'
    bot.send_message(message.chat.id, text)
    data_curr.append(quote)
    bot.register_next_step_handler(message, amount_handler, data_curr)


def amount_handler(message: telebot.types.Message, data_curr):
    amount = message.text.strip()
    try:
        base, quote = data_curr
        conv = Converter.get_price(base, quote, amount)
    except ValueError as e:
        bot.reply_to(message, f'Системная ошибка. Введите команду /help, или /convert')
    except APIException as e:
        bot.send_message(message.chat.id, f'Ошибка в конвертации:\n{e}')
    else:
        answer_text = f'Стоимость {amount} едениц валюты {base} в валюте {quote}: {round(conv, 3)} \
\n\n{amount} {DATA_TICKER[base]} = {round(conv, 3)} {DATA_TICKER[quote]}'
        bot.send_message(message.chat.id, answer_text, reply_markup=commands_markup())


@bot.message_handler(content_types=['text'])
def handle_converter(message: telebot.types.Message):
    try:
        base, quote, amount = message.text.split()
    except ValueError:
        bot.reply_to(message, 'Неверное количество параметров!\nПравильный формат команды для бота можно посмотреть в \
/help. Или воспользуйся командой /convert.')
    else:
        base = base.capitalize()
        quote = quote.capitalize()
        try:
            conv = Converter.get_price(base, quote, amount)
            answer_text = f'Стоимость {amount} едениц валюты {base} в валюте {quote}: {round(conv, 3)} \
\n\n{amount} {DATA_TICKER[base]} = {round(conv, 3)} {DATA_TICKER[quote]}'
            bot.reply_to(message, answer_text, reply_markup=commands_markup())
        except APIException as e:
            bot.reply_to(message, f'Ошибка в команде:\n{e}')
        except Exception as e:
            bot.reply_to(message, f'Системная ошибка.\n{e}')


bot.polling(none_stop=True)
