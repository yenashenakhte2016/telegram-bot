import math
from sqlite3 import OperationalError

chat_id = int
chat_name = str


def main(tg):
    global chat_id, chat_name
    chat_id = tg.chat_data['chat']['id']
    chat_name = "chat{}stats".format(str(chat_id).replace('-', ''))
    if tg.message:
        tg.send_chat_action('typing')
        tg.send_message("Loading....")
        if tg.message['matched_regex'] == '^/stats$':
            check_status(tg)
        else:
            tg.edit_message_text("....")
    else:
        opt_in(tg)


def opt_in(tg):
    db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    if db_selection:
        tg.answer_callback_query("Chat stats are already enabled!")
    elif check_if_mod(tg):
        tg.database.insert("chat_opt_status", {"status": True, "chat_id": chat_id})
        tg.answer_callback_query("You have opted in!")
    else:
        tg.answer_callback_query("Only moderators can enable chat stats!")


def check_status(tg):
    try:
        db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    except OperationalError:
        tg.database.create_table("chat_opt_status", {"chat_id": "TEXT UNIQUE", "status": "BOOLEAN"})
        db_selection = tg.database.select("chat_opt_status", ["status"], {"chat_id": chat_id, "status": True})
    if db_selection:
        try:
            db_selection = tg.database.select(chat_name, ["AVG(char_length)", "COUNT(*)"])
        except OperationalError:
            tg.edit_message_text("Error, try again later")
            return
        avg_char_length = math.ceil(db_selection[0]['AVG(char_length)'])
        total_sent = db_selection[0]['COUNT(*)']
        tg.database.execute("select message_type, count(*) from {} group by message_type;".format(chat_name))
        message = "<b>Total messages sent:</b> {}\n\n<b>Average word length:</b> {}\n".format(total_sent,
                                                                                                avg_char_length)
        for result in tg.database.db:
            message += "\n<b>{}s:</b> {}".format(result[0].title(), result[1])
        tg.edit_message_text(message,
                             parse_mode="HTML")
    else:
        keyboard = [[{'text': 'Enable Stats', 'callback_data': '%%toggle_on%%'}]]
        tg.edit_message_text(
            "You are currently not opted into stat collection. A moderator can opt-in by clicking this button.",
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
    'permissions': True
}

arguments = {
    'text': [
        "^/stats$",
        "^/chatstats opt-out$"
    ]
}
