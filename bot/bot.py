import asyncio
import re
import time
import traceback

import telebot
from telethon.tl.functions.channels import GetChannelsRequest

from PROPERTY import ONO_BOT_PROPS, PROPS
from dao_layer import retrieve_all_channels, add_anchor, add_user_channel_row, retrieve_all_messages_with_channel
from index import InvertedIndex
from logger import log
from properties_bot import EMOJI

bot = telebot.TeleBot(ONO_BOT_PROPS.token)
client = PROPS.client_bot
client.start()

loop = asyncio.get_event_loop()
last_time_query = 0
index: InvertedIndex = None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "Готов к работе. "
        f"\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n#add <id канала>"

        f"\n\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n#search <набор слов, любое выражение> "
        "\nи я поищу новости этому отвечающие."
    )


@bot.message_handler(regexp='^#add\s(\w|\W)*')
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

REGEX_HTML_CLEANER = re.compile('<.*?>')
def clean_html(raw_html):
    return re.sub(REGEX_HTML_CLEANER, '', raw_html)

@bot.message_handler(regexp='^#search\s(\w|\W)*')
def search(message):
    query = message.html_text[len('#search'):].strip()
    rebuild_index()
    result = index.search_phrase(query)

    for ((channel_name, msg_id), match) in result:
        msg = list(client.iter_messages(entity=channel_name, ids=int(msg_id)))[0]
        text = msg.text
        title = msg.chat.title
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
        try:
            loop.run_until_complete(client(GetChannelsRequest(channel_to_check)))
        except Exception as e:
            stack_trace = traceback.format_exc()
            log("Error while connecting to PostgreSQL " + str(e) + "\n" + str(stack_trace))
            return False
    return True


def available_channels(client):
    chats = [chat.name for chat in list(client.iter_dialogs())]
    return chats


bot.polling(none_stop=True, interval=0)