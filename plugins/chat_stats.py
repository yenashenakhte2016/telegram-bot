import math
from sqlite3 import OperationalError, IntegrityError

chat_id = int
chat_name = str

types = ["audio", "document", "photo", "sticker", "video", "voice", "contact", "location", "venue", "text"]
pretty_types = ["Audio", "Documents", "Photos", "Stickers", "Videos", "Voice", "Contacts", "Locations", "Venues",
                "Text"]


def main(tg):
    global chat_id, chat_name
    chat_id = tg.chat_data['chat']['id']
    chat_name = "chat{}stats".format(str(chat_id).replace('-', ''))
    if tg.message:
        tg.send_chat_action('typing')
        if tg.message['matched_regex'] == arguments['text'][0]:
            tg.send_message("Loading....")
            check_status(tg)
        elif tg.message['matched_regex'] == arguments['text'][2]:
            tg.send_message("Loading....")
            user_stats(tg)
        elif tg.message['matched_regex'] == arguments['text'][1]:
            opt_out(tg)
    elif tg.callback_query:
        if tg.callback_query['data'] == '%%toggle_on%%':
            opt_in(tg)
        elif tg.callback_query['data'] == '%%toggle_off%%':
            opt_out(tg)


def opt_in(tg):
    db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    if db_selection:
        tg.answer_callback_query("Chat stats are already enabled!")
    elif check_if_mod(tg):
        try:
            tg.database.insert("chat_opt_status", {"status": True, "chat_id": chat_id})
        except IntegrityError:
            tg.database.update("chat_opt_status", {"status": True}, {"chat_id": chat_id})
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
            tg.database.update("chat_opt_status", {"status": False}, {"chat_id": chat_id})
            tg.answer_callback_query()
            tg.edit_message_text("You have successfully disabled statistics. All chat data has been deleted.",
                                 message_id=tg.callback_query['message']['message_id'])
        else:
            tg.answer_callback_query("Only mods can disable stats!")
    elif tg.message:
        db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
        if db_selection:
            keyboard = [[{'text': 'Disable & Remove Stats', 'callback_data': '%%toggle_off%%'}]]
            tg.send_message("Are you sure you want to opt-out? All chat data is deleted, this is irreversible.",
                            reply_markup=tg.inline_keyboard_markup(keyboard))
        else:
            tg.send_message("You aren't currently opted in")
    return


def check_status(tg):
    try:
        db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    except OperationalError:
        tg.database.create_table("chat_opt_status", {"chat_id": "TEXT UNIQUE", "status": "BOOLEAN"})
        db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    if db_selection:
        give_stats(tg)
    else:
        keyboard = [[{'text': 'Enable Stats', 'callback_data': '%%toggle_on%%'}]]
        tg.edit_message_text(
            "You are not opted into stat collection. A moderator can opt-in by clicking this button.",
            parse_mode="HTML",
            reply_markup=tg.inline_keyboard_markup(keyboard))


def give_stats(tg):
    try:
        db_selection = tg.database.select(chat_name, ["char_length", "message_type", "time"])
    except OperationalError:
        tg.edit_message_text("Error, try again later")
        return
    if len(db_selection) < 100:
        tg.edit_message_text("Still collecting data. Check back in a bit.")
        return

    message = "<b>Global Chat Stats:</b>\n\n".format(tg.message['chat']['title'])
    message += create_message(*parse_db_result(db_selection))

    tg.edit_message_text(message, parse_mode="HTML")


def create_message(total_messages, total_characters, message_types, times, average_length):
    message = "<b>Total Messages Sent:</b> {:,}".format(total_messages)
    message += "\n<b>Total Characters Sent:</b> {:,}".format(total_characters)
    message += "\n<b>Average Message Length:</b> {:,}".format(average_length)

    message += "\n\n<b>Types of Messages Sent</b>"
    for msg_type, total in message_types.items():
        message += "\n<b>{}:</b> {:,}".format(pretty_types[types.index(msg_type)], total)

    message += parse_times(times)
    return message


def parse_db_result(db_selection):
    total_messages = 0
    total_characters = 0
    message_types = dict()
    times = {
        '0to6': 0,
        '6to12': 0,
        '12to18': 0,
        '18to0': 0
    }
    for result in db_selection:
        total_messages += 1
        if result['char_length']:
            total_characters += result['char_length']
        try:
            message_types[result['message_type']] += 1
        except KeyError:
            message_types[result['message_type']] = 1

        hour_sent = ((result['time'] % 86400) / 3600)
        if hour_sent < 6:
            times['0to6'] += 1
        elif hour_sent < 12:
            times['6to12'] += 1
        elif hour_sent < 18:
            times['12to18'] += 1
        else:
            times['18to0'] += 1

    average_char_length = math.ceil(total_characters / message_types['text'])
    for k, v in times.items():
        percent = v / total_messages
        times[k] = "{:.1%}".format(percent)

    return total_messages, total_characters, message_types, times, average_char_length


def user_stats(tg):
    user_id = tg.message['reply_to_message']['from']['id'] if 'reply_to_message' in tg.message else \
        tg.message['from']['id']
    first_name = tg.message['reply_to_message']['from']['first_name'] if 'reply_to_message' in tg.message else \
        tg.message['from']['first_name']

    db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})

    if db_selection:
        db_selection = tg.database.select(chat_name, ["char_length", "message_type", "time"], {'user_id': user_id})
        if len(db_selection) > 50:
            message = "<b>{}'s Statistics</b>\n\n".format(first_name)
            message += create_message(*parse_db_result(db_selection))
            tg.edit_message_text(message, parse_mode="HTML")
        else:
            tg.edit_message_text("Still collecting stats. Check back later", parse_mode="HTML")
    else:
        tg.edit_message_text("This chat isn't opted into stat collection", parse_mode="HTML")


def parse_times(times):
    message = "<b>\n\nActivity By Time</b> <i>(UTC)</i>"
    '12 AM - 6 AM: {}\n6 AM - 12 PM\n12 PM - 6 PM\n6 PM - 12 AM'
    message += "\n<b>00:00 - 06:00:</b> {}".format(times['0to6'])
    message += "\n<b>06:00 - 12:00:</b> {}".format(times['6to12'])
    message += "\n<b>12:00 - 18:00:</b> {}".format(times['12to18'])
    message += "\n<b>18:00 - 00:00:</b> {}".format(times['18to0'])
    return message


def check_if_mod(tg):
    admins = tg.get_chat_administrators()
    user_id = tg.callback_query['from']['id']
    if admins['ok']:
        admins = admins['result']
    else:
        return
    if any(user['user']['id'] == user_id for user in admins):
        return True


plugin_parameters = {
    'name': "Chat Stats",
    'desc': "Chat and user message statistics",
    'extended_desc': "...",
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
