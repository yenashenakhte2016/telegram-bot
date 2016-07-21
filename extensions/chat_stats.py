# -*- coding: utf-8 -*-

types = ["audio", "document", "photo", "sticker", "video", "voice", "contact", "location", "venue", "text"]


def main(update, database):
    cursor = database.cursor()
    user_obj = None
    chat_obj = None
    if 'message' in update:
        user_obj = update['message']['from']
        chat_obj = update['message']['chat']
        add_message(update['message'], database, cursor)
    elif 'inline_query' in update:
        user_obj = update['inline_query']['from']
    elif 'callback_query' in update:
        user_obj = update['callback_query']['from']
    if user_obj:
        cursor.execute("INSERT INTO users_list VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                       "first_name=%s, last_name=%s, user_name=%s", add_user(user_obj))
    if chat_obj:
        cursor.execute("INSERT INTO chats_list VALUES(%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE "
                       "title=%s, username=%s, first_name=%s, last_name =%s", add_chat(update['message']['chat']))
    database.commit()
    cursor.close()


def add_message(message, database, cursor):
    database.query("SELECT status FROM chat_opt_status WHERE chat_id={}".format(message['chat']['id']))
    result = database.store_result().fetch_row(how=1)
    if result and result[0]['status']:
        user_id = message['from']['id']
        time = message['date']
        char_length = len(message['text']) if 'text' in message else None
        word_length = len(message['text'].split()) if 'text' in message else None
        message_type = None
        for key in types:
            if key in message:
                message_type = key
                break
        if message_type:
            cursor.execute("CREATE TABLE IF NOT EXISTS `{}stats`(user_id BIGINT NOT NULL, time_sent DATETIME NOT NULL, "
                           "char_length SMALLINT UNSIGNED, word_count SMALLINT UNSIGNED, "
                           "message_type VARCHAR(16))".format(message['chat']['id']))
            values = (user_id, time, char_length, word_length, message_type)
            cursor.execute(
                "INSERT INTO `{}stats` VALUES(%s, FROM_UNIXTIME(%s), %s, %s, %s)".format(message['chat']['id']), values)


def add_user(user):
    user_id = user['id']
    first_name = user['first_name']
    last_name = user['last_name'] if 'last_name' in user else None
    username = user['username'] if 'username' in user else None
    entry = (user_id, first_name, last_name, username, first_name, last_name, username)
    return entry


def add_chat(chat):
    chat_id = chat['id']
    chat_type = chat['type']
    title = chat['title'] if 'title' in chat else None
    username = chat['username'] if 'username' in chat else None
    first_name = chat['first_name'] if 'first_name' in chat else None
    last_name = chat['last_name'] if 'last_name' in chat else None
    entry = (chat_id, chat_type, title, username, first_name, last_name, title, username, first_name, last_name)
    return entry


def init_db(database):
    cursor = database.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users_list(user_id BIGINT UNIQUE NOT NULL, first_name VARCHAR(128) NOT NULL,"
        "last_name VARCHAR(128), user_name VARCHAR(128)) CHARACTER SET utf8mb4;")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS chats_list(chat_id BIGINT UNIQUE NOT NULL, chat_type VARCHAR(24) NOT NULL,"
        "title VARCHAR(128), username VARCHAR(128), first_name VARCHAR(128), last_name VARCHAR(128)) "
        "CHARACTER SET utf8mb4;")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS chat_opt_status(chat_id BIGINT UNIQUE NOT NULL, status BOOLEAN NOT NULL, "
        "toggle_user BIGINT NOT NULL, toggle_date DATETIME NOT NULL) CHARACTER SET utf8mb4;")
    cursor.close()
