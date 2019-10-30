from telethon import TelegramClient


class PROPS:
    api_id = some_number
    api_hash = 'put it here'
    client = TelegramClient('session_name', api_id, api_hash)
    sleep_time = 15 #* 60


class DATA_BASE_PROPS:
    host = 'localhost'
    database = 'postgres'
    user = 'postgres'
    password = 'pass'
    port = 5433


class ONO_BOT_PROPS:
    token = 'token'