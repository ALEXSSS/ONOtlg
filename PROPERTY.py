from telethon import TelegramClient


class PROPS:
    api_id = 123
    api_hash = 'hash'
    client = TelegramClient('session_name', api_id, api_hash)
    sleep_time_approaches = 5  # * 60
    sleep_time_channel = 2.0


class DATA_BASE_PROPS:
    host = 'localhost'
    database = 'postgres'
    user = 'postgres'
    password = 'kinmanz'
    port = 5433


# Do not forget VPN
class ONO_BOT_PROPS:
    token = 'token'
