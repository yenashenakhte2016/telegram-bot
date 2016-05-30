from sqlite3 import OperationalError


def main(update, database, pers_data):
    for result in update:
        if 'message' in result:
            chat_id = result['message']['chat']['id']
            try:
                db_selection = database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
            except OperationalError:
                database.create_table("chat_opt_status", {"chat_id": "TEXT UNIQUE", "status": "BOOLEAN"})
                db_selection = database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
            if db_selection:
                add_message(database, result['message'])
    return pers_data


def add_message(database, message):
    types = ["audio", "document", "photo", "sticker", "video", "voice", "contact", "location", "venue", "text"]
    chat_name = "chat{}stats".format(str(message['chat']['id']).replace('-', ''))
    user_id = message['from']['id']
    time = message['date']
    char_length = len(message['text']) if 'text' in message else None
    for message_type in types:
        if message_type in message:
            try:
                database.insert(chat_name,
                                {'user_id': user_id, 'time': time, 'char_length': char_length,
                                 'message_type': message_type})
            except OperationalError:
                database.create_table(chat_name,
                                      {"user_id": "INT", "time": "INT", "char_length": "INT", "message_type": "TEXT"})
                database.insert(chat_name,
                                {'user_id': user_id, 'time': time, 'char_length': char_length,
                                 'message_type': message_type})
            return
