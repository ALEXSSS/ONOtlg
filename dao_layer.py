import traceback

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from PROPERTY import DATA_BASE_PROPS
from logger import log

# TODO ADD multithreaded pooling
# TODO Add multithreaded connection pool

pool = ThreadedConnectionPool(
    user=DATA_BASE_PROPS.user,
    password=DATA_BASE_PROPS.password,
    host=DATA_BASE_PROPS.host,
    port=DATA_BASE_PROPS.port,
    database=DATA_BASE_PROPS.database,
    maxconn=DATA_BASE_PROPS.connections,
    minconn=1
)


def with_postgres_cursor(f):
    def wrapper(*args, **kwargs):
        connection = pool.getconn()
        cursor = None
        try:
            cursor = connection.cursor()
            f.connection = connection
            f.cursor = cursor
            return f(cursor, *args, **kwargs)
        except (Exception, psycopg2.Error) as error:
            stack_trace = traceback.format_exc()
            log("Error while connecting to PostgreSQL" + str(error) + "\n" + str(stack_trace))
        finally:
            if connection:
                cursor.close()
                connection.commit()
                pool.putconn(connection)
                log("PostgreSQL connection is returned to the pool!")

    return wrapper


@with_postgres_cursor
def retrieve_all_channels(cursor):
    cursor.execute("SELECT * from ono_anchors;")
    return list(cursor.fetchall())


@with_postgres_cursor
def retrieve_all_messages_with_channel(cursor):
    cursor.execute(
        "SELECT content, channel_name, message_id from message where publish_date > now() - interval '1 month';")
    return list(cursor.fetchall())


@with_postgres_cursor
def retrieve_all_channels_for_user(cursor, user_id):
    cursor.execute(
        f"""
        SELECT chanel_name FROM user_channel WHERE user_id = '{user_id}';
        """
    )
    return list(cursor.fetchall())


@with_postgres_cursor
def retrieve_all_messages_with_ids(cursor, ids=[]):
    cursor.execute(
        f"""
        SELECT content, channel_name, message_id 
        from message 
        where message_id in ({','.join(ids)});
        """
    )
    return list(cursor.fetchall())


@with_postgres_cursor
def retrieve_messages_from_anchor_with_channel(cursor):
    pass


@with_postgres_cursor
def initialise_anchor(cursor, channel, anchor):
    cursor.execute("UPDATE ono_anchors SET last_message_id = '{}' WHERE chanel_name = '{}';".format(anchor, channel))


@with_postgres_cursor
def add_anchor(cursor, channel):
    cursor.execute("INSERT INTO ono_anchors(CHANEL_NAME) VALUES ('{}');".format(channel))


@with_postgres_cursor
def add_user_channel_row(cursor, channel, user_id):
    cursor.execute("INSERT INTO user_channel(CHANEL_NAME, USER_ID) VALUES ('{}','{}');".format(channel, user_id))


@with_postgres_cursor
def delete_user_channel_row(cursor, channel, user_id):
    cursor.execute("delete from user_channel where chanel_name = '{}' and user_id = '{}';".format(channel, user_id))


@with_postgres_cursor
def insert_messages(cursor, channel, messages):
    for message in messages:
        # message.chat.id
        # message.chat.title
        # message.date
        # message.sender.username
        # message.sender.id

        if not message.text or message.text.isspace():
            continue

        cursor.execute(
            """
                INSERT INTO MESSAGE(
                    MESSAGE_ID,
                    
                    CHANNEL_ID,
                    CHANNEL_NAME,
                    CHANNEL_TITLE,
                    
                    SENDER_USERNAME,
                    SENDER_ID,
                    
                    PUBLISH_DATE,
                    CONTENT
                ) VALUES (
                    '{}',
                    
                    '{}',
                    '{}',
                    '{}',
                    
                    '{}',
                    '{}',
                    
                    '{}',
                    '{}'
                );
            """.format(message.id, message.chat.id, channel, message.chat.title if hasattr(message.chat, 'title') else "",
                       message.sender.username, message.sender.id, message.date, message.text)
        )

# CREATE TABLE MESSAGE
# (
#     MESSAGE_ID   TEXT,
#
#     CHANNEL_ID TEXT,
#     CHANNEL_NAME TEXT,
#     CHANNEL_TITLE TEXT,
#
#     SENDER_NAME TEXT,
#     SENDER_USERNAME TEXT,
#
#     PUBLISH_DATE TEXT,
#     CONTENT      TEXT NOT NULL,
#     PRIMARY KEY (MESSAGE_ID, CHANNEL_NAME)
# );
