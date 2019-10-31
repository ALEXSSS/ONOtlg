import time

from PROPERTY import PROPS
from dao_layer import retrieve_all_channels, initialise_anchor, insert_messages
from logger import log


def aggregate_massages():
    tg_client = PROPS.client
    tg_client.start()

    while True:
        for channel, last_message in retrieve_all_channels():
            log(f"Check channel : {channel}")
            if last_message == 'NOT_SET':
                message = list(tg_client.iter_messages(entity=channel, limit=1))[0]
                initialise_anchor(channel, message.id)
                log(f"Anchor set {channel}: {message.id}")
            else:
                time.sleep(PROPS.sleep_time_channel)
                messages = [*tg_client.iter_messages(entity=channel, min_id=int(last_message) + 1)]
                if len(messages) > 0:
                    initialise_anchor(channel, max([message.id for message in messages]))
                    insert_messages(channel, messages)
                for item in messages:
                    log(f"Taken from the chat {channel},\n text: ", item.text)
        time.sleep(PROPS.sleep_time_approaches)


if __name__ == '__main__':
    log("Start messages aggregation: ")
    aggregate_massages()
