from telethon import TelegramClient


PROD = False
# PROD = True


class PROPS:
    api_id = 123
    api_hash = 'hash'
    client_extractor = TelegramClient('extractor_session', api_id, api_hash)
    client_bot = TelegramClient('bot_session', api_id, api_hash)
    sleep_time_approaches = 15 * 60
    sleep_time_channel = 3


class DATA_BASE_PROPS:
    host = 'localhost'
    database = 'postgres'
    user = 'postgres'
    password = 'pass'
    port = 5434
    connections = 20


# Do not forget VPN
class ONO_BOT_PROPS:
    token = 'token'
