# -*- coding: utf-8 -*-


import random

responses = ["Ok, I will remind you in", "I'll be sure to remind you in", "Expect to hear from me in",
             "I'll be sure to ping you in", "You will hear from me in", "You'll receive a notification in"]
prefixes = ['to', 'that']


def main(tg):
    tg.cursor.execute("CREATE TABLE IF NOT EXISTS remind_plugin(time_id VARCHAR(128), user_id BIGINT NOT NULL, "
                      "chat_id BIGINT NOT NULL, message_id BIGINT NOT NULL) CHARACTER SET utf8;")
    if tg.message:
        if tg.plugin_data:
            statement = 'SELECT message_id FROM remind_plugin WHERE time_id="{}"'.format(tg.message['time_id'])
            tg.database.query(statement)
            query = tg.database.store_result()
            result = query.fetch_row(maxrows=0)
            message_id = result[0][0]
            tg.edit_message_reply_markup(message_id=message_id, chat_id=tg.message['chat']['id'])
            tg.send_message("Reminder:\n{}".format(tg.plugin_data))
        else:
            tg.send_chat_action('typing')
            reminder_time = added_time(tg.message['match'][0], tg.message['match'][1]) + tg.message['date']
            if reminder_time:
                reminder_message = remove_prefix(tg.message['match'][2])
                time_id = tg.flag_time(reminder_time, reminder_message)

                message = create_message(tg.message)
                keyboard = [[{'text': "Cancel", 'callback_data': 'cancel{}'.format(time_id)},
                             {'text': "Add Time", 'callback_data': 'add{}'.format(time_id)}]]
                message = tg.send_message(message, reply_markup=tg.inline_keyboard_markup(keyboard))
                if message['ok']:
                    message_id = message['result']['message_id']
                    user_id = tg.message['from']['id']
                    chat_id = tg.message['chat']['id']
                    tg.cursor.execute("INSERT INTO remind_plugin VALUES(%s, %s, %s, %s)",
                                      (time_id, user_id, chat_id, message_id))
            else:
                tg.send_message("Invalid Time :(")
    else:
        if 'add' in tg.callback_query['data']:
            time_id = tg.callback_query['data'].replace('add', '')
            permission = check_user(time_id, tg.callback_query['message']['chat']['id'],
                                    tg.callback_query['from']['id'], tg.database)
            if permission:
                tg.answer_callback_query()
                keyboard = [[{'text': "+5", 'callback_data': '+05{}'.format(time_id)},
                             {'text': "+15", 'callback_data': '+15{}'.format(time_id)},
                             {'text': "+30", 'callback_data': '+30{}'.format(time_id)},
                             {'text': "+60", 'callback_data': '+60{}'.format(time_id)}]]
                tg.edit_message_reply_markup(reply_markup=tg.inline_keyboard_markup(keyboard))
            else:
                tg.answer_callback_query("You aren't the one who set the reminder!")
        elif 'cancel' in tg.callback_query['data']:
            time_id = tg.callback_query['data'].replace('cancel', '')
            tg.answer_callback_query("Successfully Cancelled")
            tg.edit_message_text("Cancelled Reminder")
            tg.cursor.execute("DELETE FROM `flagged_time` WHERE time_id=%s", (time_id,))
        elif '+' in tg.callback_query['data']:
            time_id = tg.callback_query['data'][3:]
            permission = check_user(time_id, tg.callback_query['message']['chat']['id'],
                                    tg.callback_query['from']['id'], tg.database)
            if permission:
                time = int(tg.callback_query['data'][1:3])
                tg.answer_callback_query("Delayed the reminder by {} minutes!".format(time))
                keyboard = [[{'text': "Cancel", 'callback_data': 'cancel{}'.format(time_id)},
                             {'text': "Add Time", 'callback_data': 'add{}'.format(time_id)}]]
                tg.edit_message_reply_markup(reply_markup=tg.inline_keyboard_markup(keyboard))
                tg.cursor.execute("UPDATE `flagged_time` SET argument_time=ADDTIME(argument_time, %s) WHERE "
                                  "time_id=%s", (time * 60, time_id))


def check_user(time_id, chat_id, user_id, database):
    statement = 'SELECT user_id FROM `remind_plugin` WHERE time_id="{}" AND chat_id={}'.format(time_id, chat_id)
    database.query(statement)
    query = database.store_result()
    result = query.fetch_row(maxrows=0)
    if result and result[0][0]:
        return True if result[0][0] == user_id else False
    else:
        return False


def added_time(time, unit):
    if "second" in unit:
        multiplier = 1
    elif "minute" in unit:
        multiplier = 60
    elif "hour" in unit:
        multiplier = 3600
    return (int(time) * multiplier) if int(time) > 0 else None


def remove_prefix(message):
    for prefix in prefixes:
        if message[:len(prefix) + 1] == prefix + ' ':
            return message[len(prefix) + 1:]
    return message


def create_message(message):
    time = int(message['match'][0])
    unit = None
    if message['match'][1] == 's' or "second" in message['match'][1]:
        unit = "second"
    elif message['match'][1] == 'm' or "minute" in message['match'][1]:
        unit = "minute"
    elif message['match'][1] == 'd' or "hour" in message['match'][1]:
        unit = "day"
    unit = unit if time == 1 else (unit + 's')
    return "{} {} {}".format(random.choice(responses), time, unit)


parameters = {
    'name': "Remind",
    'short_description': "The remind plugin gives you a notification at the time you specify",
    'long_description': "The remind plugins pings you at a time you specify. To cancel the reminder you just have to "
                        "delete the message which triggered it. Here's an example: \n<code>Remind me in 30 minutes to "
                        "take out the trash</code>",
    'permissions': True
}

arguments = {
    'text': [
        "(?i)remind .* (\d+)([smd]) (.*)",
        "(?i)remind .* (\d+) (seconds|minutes|hours) (.*)",
        "(?i)remind .* (\d+) (second|minute|hour) (.*)",
    ]
}
