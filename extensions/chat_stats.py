from sqlite3 import OperationalError, IntegrityError


chat_id = None


def main(update, database):
    for result in update:
        if 'message' in result:
            result = result['message']
            global chat_id
            chat_id = result['chat']['id']
            add_message(database, result)
            add_user(database, result['from'])
            add_chat(database, result['chat'])


def add_message(database, message):
    try:
        db_selection = database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    except OperationalError:
        database.create_table("chat_opt_status", {"chat_id": "TEXT UNIQUE", "status": "BOOLEAN"})
        db_selection = database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    if db_selection:
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
                                          {"user_id": "INT", "time": "INT", "char_length": "INT",
                                           "message_type": "TEXT"})
                    database.insert(chat_name,
                                    {'user_id': user_id, 'time': time, 'char_length': char_length,
                                     'message_type': message_type})
                return


def add_user(database, user):
    username = user['username'] if 'username' in user else None
    last_name = user['last_name'] if 'last_name' in user else None
    try:
        database.insert("user_list", {'first_name': user['first_name'], 'last_name': last_name, 'username': username,
                                      'id': user['id']})
    except IntegrityError:
        database.update("user_list",
                        {'first_name': user['first_name'], 'last_name': last_name, 'username': username},
                        {'id': user['id']})
    except OperationalError:
        database.create_table("user_list", {'id': "INT NOT NULL PRIMARY KEY", 'first_name': 'text', 'last_name': 'text',
                                            'username': 'text'})


def add_chat(database, chat):
    title = chat['title'] if 'title' in chat else None
    username = chat['username'] if 'username' in chat else None
    first_name = chat['first_name'] if 'first_name' in chat else None
    last_name = chat['last_name'] if 'last_name' in chat else None

    try:
        database.insert("chat_list", {'id': chat['id'], 'type': chat['type'], 'title': title, 'username': username,
                                      'first_name': first_name, 'last_name': last_name})
    except IntegrityError:
        database.update("chat_list", {'type': chat['type'], 'title': title, 'username': username,
                                      'first_name': first_name, 'last_name': last_name}, {'id': chat['id']})
    except OperationalError:
        updated = False
        database.create_table("chat_list",
                              {'id': "INT NOT NULL PRIMARY KEY", 'type': "text", 'title': "text", 'username': 'text',
                               'first_name': 'text', 'last_name': 'text'})
