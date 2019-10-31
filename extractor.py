import time

from PROPERTY import PROPS
from dao_layer import retrieve_all_channels, initialise_anchor, insert_messages
from logger import log


def run():
    ono_client = PROPS.client
    ono_client.start()

    while True:
        for channel, last_message in retrieve_all_channels():
            if last_message == 'NOT_SET':
                message = list(ono_client.iter_messages(entity=channel, limit=1))[0]
                initialise_anchor(channel, message.id)
                print(message.text)
            else:
                messages = list(ono_client.iter_messages(entity=channel, min_id=int(last_message)))
                # remove_last_min_one
                messages = [message for message in messages if message.id != last_message]
                if len(messages) > 0:
                    initialise_anchor(channel, max([message.id for message in messages]))
                    insert_messages(channel, messages)
                for item in messages: log(f"Taken from the chat {channel},\n text: ", item.text)
        time.sleep(PROPS.sleep_time)


run()
