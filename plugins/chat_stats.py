import _mysql_exceptions

chat_id = int
chat_name = str

types = ["audio", "document", "photo", "sticker", "video", "voice", "contact", "location", "venue", "text"]
pretty_types = ["Audio", "Documents", "Photos", "Stickers", "Videos", "Voice", "Contacts", "Locations", "Venues",
                "Text"]


def main(tg):
    global chat_id
    chat_id = tg.chat_data['chat']['id']
    if tg.message:
        tg.send_chat_action('typing')
        if tg.message['matched_regex'] == arguments['text'][1]:
            opt_out(tg)
        else:
            if check_status(tg.database):
                if tg.message['matched_regex'] == arguments['text'][0]:
                    chat_stats(tg)
                elif tg.message['matched_regex'] == arguments['text'][2]:
                    user_stats(tg)
            else:
                keyboard = [[{'text': 'Enable Stats', 'callback_data': '%%toggle_on%%'}]]
                message = "You are not opted into stat collection. A moderator can opt-in by clicking this button."
                tg.send_message(message, reply_markup=tg.inline_keyboard_markup(keyboard))
    elif tg.callback_query:
        if tg.callback_query['data'] == '%%toggle_on%%':
            opt_in(tg)
        elif tg.callback_query['data'] == '%%toggle_off%%':
            opt_out(tg)


def opt_in(tg):
    if check_status(tg.database):
        tg.answer_callback_query("Chat stats are already enabled!")
    elif check_if_mod(tg):
        user_id = tg.callback_query['from']['id']
        try:
            tg.cursor.execute("INSERT INTO chat_opt_status VALUES(%s, 1, %s, now())", (chat_id, user_id))
        except _mysql_exceptions.IntegrityError:
            tg.cursor.execute("UPDATE chat_opt_status SET status=1, toggle_user=%s, toggle_date=now()", (user_id,))
        tg.answer_callback_query("You have opted in!")
        tg.edit_message_text("You have successfully opted into stat collection."
                             "You'll be able to see statistics shortly. Opt out at anytime using /chatstats opt-out",
                             message_id=tg.callback_query['message']['message_id'])
    else:
        tg.answer_callback_query("Only moderators can enable chat stats!")


def opt_out(tg):
    if tg.callback_query:
        if check_if_mod(tg):
            tg.database.drop_table(chat_name)
            tg.cursor.execute("UPDATE chat_opt_status SET status=FALSE AND toggle_user=%s AND toggle_date=now() WHERE"
                              "chat_id=%s", (tg.callback_query['from']['id'], chat_id))
            tg.answer_callback_query()
            tg.edit_message_text("You have successfully disabled statistics. All chat data has been deleted.",
                                 message_id=tg.callback_query['message']['message_id'])
        else:
            tg.answer_callback_query("Only mods can disable stats!")
    elif tg.message:
        tg.database.query("SELECT status FROM chat_opt_status WHERE chat_id=%s AND status=TRUE".format(chat_id))
        query = tg.database.store_result()
        rows = query.fetch_row()
        if rows:
            keyboard = [[{'text': 'Disable & Remove Stats', 'callback_data': '%%toggle_off%%'}]]
            tg.send_message("Are you sure you want to opt-out? All chat data is deleted, this is irreversible.",
                            reply_markup=tg.inline_keyboard_markup(keyboard))
        else:
            tg.send_message("You aren't currently opted in")
    return


def chat_stats(tg):
    total_messages, total_characters, average_chars, total_words = metrics(tg.database)
    message = "<b>Global Chat Stats:</b>\n\n".format(tg.message['chat']['title'])
    message += "<b>Total Messages Sent:</b> {:,}".format(total_messages)
    message += "\n<b>Total Characters Sent:</b> {:,}".format(total_characters)
    message += "\n<b>Average Characters Per Message:</b> {0:.1f}".format(average_chars)

    message += "\n\n<b>Types of Messages Sent</b>"
    message_types = types_breakdown(tg.database)
    for msg_type, total in message_types.items():
        message += "\n<b>{}:</b> {:,}".format(pretty_types[types.index(msg_type)], total)

    message += hourly_time(total_messages, tg.database)
    tg.send_message(message)


def user_stats(tg):
    user_id = tg.message['reply_to_message']['from']['id'] if 'reply_to_message' in tg.message else \
        tg.message['from']['id']
    first_name = tg.message['reply_to_message']['from']['first_name'] if 'reply_to_message' in tg.message else \
        tg.message['from']['first_name']
    total_messages, total_characters, average_chars, total_words = metrics(tg.database, user_id)

    message = "<b>{}'s Chat Stats</b>\n\n".format(first_name)
    message += "<b>Total Messages Sent:</b> {:,}".format(total_messages)
    message += "\n<b>Total Characters Sent:</b> {:,}".format(total_characters)
    message += "\n<b>Average Characters Per Message:</b> {0:.1f}".format(average_chars)

    message += "\n\n<b>Types of Messages Sent</b>"
    message_types = types_breakdown(tg.database)
    for msg_type, total in message_types.items():
        message += "\n<b>{}:</b> {:,}".format(pretty_types[types.index(msg_type)], total)

    message += hourly_time(total_messages, tg.database)

    tg.send_message(message)


def types_breakdown(database, user_id=None):
    message_types = dict()
    statement = "SELECT message_type, COUNT(*) FROM `{}stats` GROUP BY message_type;".format(chat_id)
    if user_id:
        statement += " WHERE user_id={}".format(user_id)
    database.query("SELECT message_type, COUNT(*) FROM `{}stats` GROUP BY message_type;".format(chat_id))
    query = database.store_result()
    rows = query.fetch_row(maxrows=0)
    for result in rows:
        message_types[result[0]] = result[1]
    return message_types


def metrics(database, user_id=None):
    statement = "SELECT COUNT(*), SUM(char_length), AVG(char_length), SUM(word_count) FROM `{}stats`".format(chat_id)
    if user_id:
        statement += " WHERE user_id={}".format(user_id)
    database.query(statement)
    query = database.store_result()
    rows = query.fetch_row(maxrows=0)[0]
    return rows[0], rows[1], rows[2], rows[3]


def hourly_time(total, database):
    database.query("SELECT hour(time_sent), Count(*) FROM `{}stats` GROUP BY HOUR(time_sent);".format(chat_id))
    query = database.store_result()
    rows = query.fetch_row(maxrows=0)
    times = {
        '0to6': 0,
        '6to12': 0,
        '12to18': 0,
        '18to0': 0
    }
    for result in rows:
        if result[0] < 6:
            times['0to6'] += result[1]
        elif result[0] < 12:
            times['6to12'] += result[1]
        elif result[0] < 18:
            times['12to18'] += result[1]
        else:
            times['18to0'] += result[1]
    return parse_times(total, times)


def parse_times(total, times):
    message = "<b>\n\nActivity By Time</b>"
    '12 AM - 6 AM: {}\n6 AM - 12 PM\n12 PM - 6 PM\n6 PM - 12 AM'
    message += "\n<b>00:00 - 06:00:</b> {:.1f}%".format((times['0to6'] / total) * 100)
    message += "\n<b>06:00 - 12:00:</b> {:.1f}%".format((times['6to12'] / total) * 100)
    message += "\n<b>12:00 - 18:00:</b> {:.1f}%".format((times['12to18'] / total) * 100)
    message += "\n<b>18:00 - 00:00:</b> {:.1f}%".format((times['18to0'] / total) * 100)
    return message


def check_status(database):
    database.query("SELECT status FROM chat_opt_status WHERE status=True and chat_id={}".format(chat_id))
    query = database.store_result()
    rows = query.fetch_row()
    return True if rows else False


def check_if_mod(tg):
    admins = tg.get_chat_administrators()
    user_id = tg.callback_query['from']['id']
    if admins['ok']:
        admins = admins['result']
    else:
        return
    if any(user['user']['id'] == user_id for user in admins):
        return True


parameters = {
    'name': "Chat Stats",
    'short_description': "Chat and user message statistics",
    'long_description': "When enabled the bot will track useful metrics related to the chat such as a time and message"
                        " type breakdowns. Collection is opt in and no actual messages are stored. You can opt out any"
                        " time using /chatstats opt-out.",
    'permissions': '10'
}

arguments = {
    'text': [
        "^/chatstats$",
        "^/chatstats opt-out$",
        "^/stats$",
        "^/userstats$"
    ]
}
