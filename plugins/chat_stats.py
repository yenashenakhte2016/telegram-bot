import math
from sqlite3 import OperationalError

chat_id = int
chat_name = str

types = ["audio", "document", "photo", "sticker", "video", "voice", "contact", "location", "venue", "text"]
pretty_types = ["Audio", "Documents", "Photos", "Stickers", "Videos", "voice", "Contacts", "Locations", "Venues",
                "Text"]


def main(tg):
    global chat_id, chat_name
    chat_id = tg.chat_data['chat']['id']
    chat_name = "chat{}stats".format(str(chat_id).replace('-', ''))
    if tg.message:
        tg.send_chat_action('typing')
        if tg.message['matched_regex'] == '^/chatstats$':
            tg.send_message("Loading....")
            check_status(tg)
        else:
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
        tg.database.insert("chat_opt_status", {"status": True, "chat_id": chat_id})
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
        try:
            db_selection = tg.database.select(chat_name, ["char_length", "message_type"])
        except OperationalError:
            tg.edit_message_text("Error, try again later")
            return
        if len(db_selection) < 250:
            tg.edit_message_text("Still collecting data. Check back in a bit.")
            return
        total_messages = 0
        total_characters = 0
        message_types = dict()
        for result in db_selection:
            total_messages += 1
            if result['char_length']:
                total_characters += result['char_length']
            try:
                message_types[result['message_type']] += 1
            except KeyError:
                message_types[result['message_type']] = 1
        message = "<b>Total Messages Sent:</b> {}\n<b>Total Characters Sent:</b> {}\n" \
                  "<b>Average Message Length:</b> {}".format(total_messages, total_characters,
                                                             math.ceil(total_characters / message_types['text']))
        message += "\n\n<b>Types of Messages Sent</b>"
        for msg_type, total in message_types.items():
            message += "\n<b>{}:</b> {}".format(pretty_types[types.index(msg_type)], total)
        tg.edit_message_text(message, parse_mode="HTML")
    else:
        keyboard = [[{'text': 'Enable Stats', 'callback_data': '%%toggle_on%%'}]]
        tg.edit_message_text(
            "You are not opted into stat collection. A moderator can opt-in by clicking this button.",
            parse_mode="HTML",
            reply_markup=tg.inline_keyboard_markup(keyboard))


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
    'permissions': 10
}

arguments = {
    'text': [
        "^/chatstats$",
        "^/chatstats opt-out$"
    ]
}
