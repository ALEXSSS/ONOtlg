import asyncio
import time
import traceback

import telebot
from telethon.tl.functions.channels import JoinChannelRequest

from PROPERTY import ONO_BOT_PROPS, PROPS
from dao_layer import retrieve_all_channels, add_anchor, add_user_channel_row, retrieve_all_messages_with_channel
from index import InvertedIndex
from logger import log

bot = telebot.TeleBot(ONO_BOT_PROPS.token)

loop = asyncio.get_event_loop()
last_time_query = 0
index = None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Готов к работе. Напишите сообщение с тегом #add <id канала>"
                          "в самом начале, и я начну его отслеживать.")


@bot.message_handler(regexp='^#add\s(\w|\W)*')
def add_channel(message):
    channel = message.html_text[len('#add'):].strip()
    channels_names = {channel[0] for channel in retrieve_all_channels()}
    if channel not in channels_names:
        if subscribe_if_not_subscribed(channel, client):
            add_anchor(channel)
            bot.reply_to(message, f"Канал будет учтён!")
        else:
            bot.reply_to(message, f"Не могу найти такой канал: {channel}")
            return
    else:
        bot.reply_to(message, f"Уже слежу за каналом, добавил вас, как заинтересованного!")
    add_user_channel_row(channel, message.from_user.id)


@bot.message_handler(regexp='^#search\s(\w|\W)*')
def search(message):
    query = message.html_text[len('#search'):].strip()
    rebuild_index()
    result = index.search_phrase(query)
    bot.reply_to(message, f"Нашли результат {result}!")


def rebuild_index():
    curr_time = time.time()
    if curr_time - last_time_query > PROPS.sleep_time_approaches:
        index = InvertedIndex()
        index.create_index(retrieve_all_messages_with_channel())


def subscribe_if_not_subscribed(channel_to_check, client):
    if channel_to_check not in available_channels(client):
        try:
            loop.run_until_complete(client(JoinChannelRequest(channel_to_check)))
        except Exception as e:
            stack_trace = traceback.format_exc()
            log("Error while connecting to PostgreSQL", str(e) + "\n" + str(stack_trace))
            return False
    return True


def available_channels(client):
    chats = [chat.name for chat in list(client.iter_dialogs())]
    return chats


bot.polling(none_stop=True, interval=0)
