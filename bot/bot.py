import asyncio
import re
import time
import functools
import traceback

from logger import log

import telebot
from telethon.tl.functions.channels import JoinChannelRequest

from PROPERTY import ONO_BOT_PROPS, PROPS
from dao_layer import retrieve_all_channels, add_anchor, add_user_channel_row, retrieve_all_messages_with_channel, \
    delete_user_channel_row, retrieve_all_channels_for_user
from index import InvertedIndex
from properties_bot import EMOJI

bot = telebot.TeleBot(ONO_BOT_PROPS.token)
# DON'T CHANGE! IT IS VERY IMPORTANT (EXACTLY CLIENT EXTRACTOR MUST BE HERE)
client = PROPS.client_extractor
client.start()

loop = asyncio.get_event_loop()
last_time_query = 0
index: InvertedIndex = None


def be_alive_after_message(error_message=None):
    def dec(func):
        @functools.wraps(func)
        def wrapper(message):
            try:
                return func(message)
            except Exception as e:
                if message is not None:
                    bot.reply_to(message, error_message)
                stack_trace = traceback.format_exc()
                log("Error: " + str(e) + "\n" + str(stack_trace))

        return wrapper

    return dec


@bot.message_handler(commands=['start', 'help'])
@be_alive_after_message("Видимо, бот сейчас не может!")
def send_welcome(message):
    bot.reply_to(
        message,
        "Готов к работе. "
        f"\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n#add <id канала>"
        "\n#unsuscribe <id канала>"

        f"\n\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n#search <набор слов, любое выражение> "
        "\nи я поищу новости этому отвечающие."

        f"\n\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n#status и я покажу все ваши каналы"
    )


@bot.message_handler(regexp='^#add\s(\w|\W)*')
@be_alive_after_message("Не могу найти канал!")
def add_channel(message):
    channel = message.html_text[len('#add'):].strip()
    channels_names = {channel[0] for channel in retrieve_all_channels()}
    if channel not in channels_names:
        if subscribe_if_not_subscribed(channel, client):
            add_anchor(channel)
            bot.reply_to(message, f"Канал добавлен!")
        else:
            bot.reply_to(message, f"Не могу найти такой канал: {channel}")
            return
    else:
        bot.reply_to(message, f"Уже слежу за каналом, добавил вас, как заинтересованного!")
    add_user_channel_row(channel, message.from_user.id)


@bot.message_handler(regexp='^#unsuscribe\s(\w|\W)*')
@be_alive_after_message("Не могу найти канал!")
def unsuscribe_channel(message):
    channel = message.html_text[len('#unsuscribe'):].strip()
    channels_names = {channel[0] for channel in retrieve_all_channels()}
    if channel not in channels_names:
        bot.reply_to(message, "Уже удалили!")
    else:
        delete_user_channel_row(channel, message.from_user.id)
        bot.reply_to(message, f"Отписал от {channel}!")


REGEX_HTML_CLEANER = re.compile('<.*?>')


def clean_html(raw_html):
    return re.sub(REGEX_HTML_CLEANER, '', raw_html)


@bot.message_handler(regexp='^#status')
@be_alive_after_message("Что-то не могу!")
def status(message):
    available_channels = {channel[0] for channel in retrieve_all_channels_for_user(message.from_user.id)}
    bot.reply_to(message, "Ваши каналы:\n" + "\n".join(available_channels))


@bot.message_handler(regexp='^#search\s(\w|\W)*')
@be_alive_after_message("Что-то не ищется!")
def search(message):
    query = message.html_text[len('#search'):].strip()
    rebuild_index()
    available_channels = {channel[0] for channel in retrieve_all_channels_for_user(message.from_user.id)}
    result = [res for res in index.search_phrase(query, limit=100) if res[0][0] in available_channels][:4]
    for ((channel_name, msg_id), match) in result:
        msg = list(client.iter_messages(entity=channel_name, ids=int(msg_id)))[0]
        text = msg.text
        title = msg.chat.title if hasattr(msg.chat, 'title') else ""
        username = msg.chat.username
        date = msg.date
        bot.send_message(
            message.chat.id,

            f"<b>TITLE</b>    : {title}"
            f"\n<b>USERNAME</b> : {username}"
            f"\n<b>DATE</b>     : {date}"
            f"\n<b>TEXT</b>     :\n{clean_html(text)}",
            parse_mode="HTML"
        )
        # loop.run_until_complete(client.forward_messages(
        #     message.chat.id,
        #     list(client.iter_messages(entity=channel_name, ids=int(msg_id)))[0]
        # ))
    bot.reply_to(message, f"Нашли результат \n{result}!")


def rebuild_index():
    global index
    curr_time = time.time()
    if not index or curr_time - last_time_query > PROPS.sleep_time_approaches:
        index = InvertedIndex()
        index.create_index(retrieve_all_messages_with_channel())


def subscribe_if_not_subscribed(channel_to_check, client):
    if channel_to_check not in available_channels(client):
        loop.run_until_complete(client(JoinChannelRequest(channel_to_check)))
    return True


def available_channels(client):
    chats = [chat.name for chat in list(client.iter_dialogs())]
    return chats


bot.polling(none_stop=True, interval=0)
