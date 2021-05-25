import asyncio
import time

from dao_layer import retrieve_all_users_notifies, retrieve_all_channels_for_user
from index import InvertedIndex, rebuild_index, FullSet
from logger import log
from PROPERTY import PROPS, ONO_BOT_PROPS

client = PROPS.client_notifier
client.start(bot_token=ONO_BOT_PROPS.token)

last_time_query = 0
index: InvertedIndex = None


async def notify_users():
    global index, last_time_query, client

    while True:
        index, last_time_query = rebuild_index(index, last_time_query)

        notifies = retrieve_all_users_notifies()

        for notify in notifies:
            user_id = notify[0]
            globally = notify[1]
            query = notify[2]

            entity = await client.get_entity(user_id)

            available_channels = {channel[0] for channel in
                                  retrieve_all_channels_for_user(user_id)} if not globally else FullSet()

            result = [res for res in index.search_phrase(query, limit=100) if res[0][0] in available_channels][:10]
            await client.send_message(entity=entity, message=str(result))
        time.sleep(PROPS.sleep_time_approaches * 2)


if __name__ == '__main__':
    log("Start user notification!")
    client.loop.run_until_complete(notify_users())

