import traceback

import psycopg2

from PROPERTY import DATA_BASE_PROPS
from logger import log


def with_postgres_cursor(f):
    def wrapper(*args, **kwargs):
        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=DATA_BASE_PROPS.user,
                                          password=DATA_BASE_PROPS.password,
                                          host=DATA_BASE_PROPS.host,
                                          port=DATA_BASE_PROPS.port,
                                          database=DATA_BASE_PROPS.database)

            cursor = connection.cursor()
            f.connection = connection
            f.cursor = cursor
            return f(cursor, *args, **kwargs)
        except (Exception, psycopg2.Error) as error:
            stack_trace = traceback.format_exc()
            log("Error while connecting to PostgreSQL", str(error) + "\n" + str(stack_trace))
        finally:
            if connection:
                connection.commit()
                cursor.close()
                connection.close()
                log("PostgreSQL connection is closed")

    return wrapper


@with_postgres_cursor
def retrieve_all_channels(cursor):
    cursor.execute("SELECT * from ono_anchors;")
    return list(cursor.fetchall())


@with_postgres_cursor
def retrieve_messages_from_anchor_with_channel(cursor):
    pass


@with_postgres_cursor
def initialise_anchor(cursor, channel, anchor):
    cursor.execute(f"UPDATE ono_anchors SET last_message_id = '{anchor}' WHERE chanel_name = '{channel}';")


@with_postgres_cursor
def add_anchor(cursor, channel):
    cursor.execute(f"INSERT INTO ono_anchors(CHANEL_NAME) VALUES ('{channel}');")


@with_postgres_cursor
def add_user_channel_row(cursor, channel, user_id):
    cursor.execute(f"INSERT INTO user_channel(CHANEL_NAME, USER_ID) VALUES ('{channel}','{user_id}');")


@with_postgres_cursor
def insert_messages(cursor, channel, messages):
    for message in messages:
        cursor.execute(f"INSERT INTO MESSAGE(MESSAGE_ID, CHANNEL_NAME, CONTENT) "
                       f"VALUES ('{message.id}','{channel}','{message.text}');")