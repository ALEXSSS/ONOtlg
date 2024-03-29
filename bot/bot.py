import asyncio
import re
import time
import functools
import traceback

from logger import log

from telethon.tl.functions.channels import JoinChannelRequest

from PROPERTY import ONO_BOT_PROPS, PROPS
from dao_layer import retrieve_all_channels, add_anchor, add_user_channel_row, retrieve_all_messages_with_channel, \
    delete_user_channel_row, retrieve_all_channels_for_user
from index import InvertedIndex, rebuild_index
from properties_bot import EMOJI

from telethon import TelegramClient, events

REGEX_HTML_CLEANER = re.compile('<.*?>')

if __name__ == "__main__":
    bot = PROPS.client_bot.start(bot_token=ONO_BOT_PROPS.token)
    client_to_manage = PROPS.client_account_manager.start()

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


@bot.on(events.NewMessage(pattern='(#|/)(start|help)'))
async def send_welcome(event):
    await event.reply(
        "Готов к работе. "
        f"\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n/add <id канала>"
        "\n/unsuscribe <id канала>"

        f"\n\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n/search <набор слов, любое выражение> "
        "\nи я поищу новости этому отвечающие в ваших выбранных ранние каналах."

        f"\n\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n/gsearch <набор слов, любое выражение> "
        "\nи я поищу новости этому отвечающие глобально среди всех мной отслеживаемых."

        f"\n\n{EMOJI.POINT_RIGHT} Напишите :"
        "\n/status и я покажу все ваши каналы"

        f"\n\n{EMOJI.POINT_RIGHT} вместо / вы можете исользовать #,"
        "\nто есть /status можно писать #status (и остальные команды)"

        f"\n\nЖелаем вам приятного поиска!"

        f"\n\n----------------------------"
        f"\n\n{EMOJI.POINT_RIGHT} более искушенные пользователи могут воспользоваться нашей notify функциональностью"
        f"\nпросто напишите /notify и набор слов в свободной форме (NOTIFY РАБОТАЕТ ТОЛЬКО ПО ВАШИМ КАНАЛАМ) /notifyg по всем каналам"
        f"\nили используйте /snotify и набор слов в ввиде логических выражений, который позволит вам лучше специфицировать ваш запрос"
        f"\nпример /snotify иван иванов and криптовалюта или пример для бьюти блоггера /snotify наташа голубой глаз and тени"
        f"\nтакже можно использовать операцию or и () скобочки для объяденения поисковых запросов, /snotifyg чтобы писать запросы по всем каналам"

        f"\n\n{EMOJI.POINT_RIGHT} используйте #set_email <email> команду, чтобы записать ваш текущий емаил для уведомлений,"
        f"\nпо умолчанию результаты поиска и нотификации приходят только в личные сообщения от бота"

        f"\n\n{EMOJI.POINT_RIGHT} используйте #set_size <number> команду, чтобы поменять дефолтный размер выборки поиска."
    )


@bot.on(events.NewMessage(pattern='^(#|/)add\s(\w|\W)+'))
async def add_channel(event):
    channel_to_add = event.message.message[len('#add'):].strip()
    channels_names = {channel[0] for channel in retrieve_all_channels()}
    if channel_to_add not in channels_names:
        result, message = await subscribe_if_not_subscribed(channel_to_add, client_to_manage)
        if result:
            add_anchor(channel_to_add)
            await event.reply(f"Канал добавлен {channel_to_add}!")
        else:
            if message == "ABSENT":
                await event.reply(f"Не могу найти такой канал: {channel_to_add}")
            else:
                await event.reply(f"Это не канал: {channel_to_add}")
            return
    else:
        await event.reply(f"Уже слежу за каналом, добавил вас, как заинтересованного!")
    add_user_channel_row(channel_to_add, event.sender_id)


@bot.on(events.NewMessage(pattern='^(#|/)unsuscribe\s(\w|\W)+'))
async def unsuscribe_channel(event):
    channel_to_remove = event.message.message[len('#unsuscribe'):].strip()
    channels_names = {channel[0] for channel in retrieve_all_channels()}
    if channel_to_remove not in channels_names:
        await event.reply("Уже удалили {channel_to_add}!")
    else:
        delete_user_channel_row(channel_to_remove, event.sender_id)
        await event.reply(f"Отписал от {channel_to_remove}!")


def clean_html(raw_html):
    return re.sub(REGEX_HTML_CLEANER, '', raw_html)


@bot.on(events.NewMessage(pattern='^(#|/)status(\s)*'))
async def status(event):
    available_channels = {channel[0] for channel in retrieve_all_channels_for_user(event.sender_id)}
    await event.reply("Ваши каналы:\n" + "\n".join(available_channels))


@bot.on(events.NewMessage(pattern='^(#|/)search\s(\w|\W)+'))
async def search(event):
    global index, last_time_query
    index, last_time_query = rebuild_index(index, last_time_query)

    query = event.message.message[len('#search'):].strip()
    available_channels = {channel[0] for channel in retrieve_all_channels_for_user(event.sender_id)}
    if len(available_channels) == 0:
        await event.reply(f"Вы еще не подписались ни на один канал, попробуйте #gsearch, чтобы поискать глобально!")
        return
    result = [res for res in index.search_phrase(query, limit=100) if res[0][0] in available_channels][:4]
    for ((channel_name, msg_id), match) in result:
        msg = (await bot.get_messages(entity=channel_name, ids=int(msg_id)))
        text = msg.message
        title = msg.chat.title if hasattr(msg.chat, 'title') else ""
        username = msg.chat.username
        date = msg.date

        chat = await event.get_input_chat()
        await bot.send_message(
            chat,
            f"<b>TITLE</b>    : {title}"
            f"\n<b>USERNAME</b> : {username}"
            f"\n<b>DATE</b>     : {date}"
            f"\n<b>METRICS</b>     : {round(match, 2)}",
            parse_mode='html'
        )
        await bot.forward_messages(
            chat,
            msg
        )
    await event.reply(f"Нашли результат \n{result}!")


@bot.on(events.NewMessage(pattern='^(#|/)gsearch\s(\w|\W)+'))
async def gsearch(event):
    global index, last_time_query
    index, last_time_query = rebuild_index(index, last_time_query)

    query = event.message.message[len('#gsearch'):].strip()
    result = [res for res in index.search_phrase(query, limit=100)][:10]
    for ((channel_name, msg_id), match) in result:
        msg = (await bot.get_messages(entity=channel_name, ids=int(msg_id)))
        text = msg.message
        title = msg.chat.title if hasattr(msg.chat, 'title') else ""
        username = msg.chat.username
        date = msg.date

        chat = await event.get_input_chat()
        await bot.send_message(
            chat,
            f"<b>TITLE</b>    : {title}"
            f"\n<b>USERNAME</b> : {username}"
            f"\n<b>DATE</b>     : {date}"
            f"\n<b>METRICS</b>     : {round(match, 2)}",
            parse_mode='html'
        )
        await bot.forward_messages(
            chat,
            msg
        )
    await event.reply(f"Нашли результат \n{result}!")


async def subscribe_if_not_subscribed(channel_to_check, client):
    async for dialog in client.iter_dialogs():
        if dialog.name == channel_to_check:
            return True, "JOINED"
    try:
        # await client(JoinChannelRequest(channel_to_check))
        log("Missed subscription")
    except ValueError as e:
        return False, "ABSENT"
    except Exception as general:
        log(f"BAD channel: {channel_to_check}, " + str(general))
        return False, "BAD"
    return True, "JOINED"


bot.run_until_disconnected()
