# -*- coding: utf-8 -*-
"""
Allows chat admins to kick and warn chat members.
"""

import datetime


def main(tg):
    """
    Routes a message to appropriate method
    """
    if tg.message['time_id']:
        unban_member(tg)
    elif check_message(tg):
        if 'reply_to_message' in tg.message:
            if tg.message['matched_regex'] in arguments['text'][0:2]:
                warn_user(tg)
            else:
                kick_user(tg)


def warn_user(tg):
    """
    Warns a user. Kicks if necessary.
    """
    max_warnings = 3
    first_name = tg.message['reply_to_message']['from']['first_name']

    user_id = tg.message['reply_to_message']['from']['id']
    warning_time = tg.message['date']
    chat_id = tg.message['chat']['id']
    if tg.message['matched_regex'] == arguments['text'][1]:
        warning_reason = tg.message['match']
    else:
        warning_reason = None
    warned_by = tg.message['from']['id']
    reply_to_message_id = tg.message['reply_to_message']['message_id']
    values = (user_id, warning_time, chat_id, warning_reason, warned_by, reply_to_message_id, 1)

    tg.cursor.execute("INSERT INTO warnings VALUES(%s, FROM_UNIXTIME(%s), %s, %s, %s, %s, %s)", values)
    tg.database.query("SELECT COUNT(*) FROM warnings WHERE user_id={} AND chat_id={} AND active_warning=1".format(
        user_id, chat_id))
    query = tg.database.store_result()
    rows = query.fetch_row()
    warning_count = rows[0][0]

    if warning_count >= max_warnings:
        kick_user(tg, from_warning=True)
    else:
        remaining_warnings = max_warnings - warning_count
        message = "{} has been warned. ".format(first_name)
        if remaining_warnings == 1:
            message += "1 warning remaining."
        else:
            message += "{} warnings remaining.".format(remaining_warnings)
        tg.send_message(message)


def kick_user(tg, from_warning=False):
    """
    Kicks a user based on inputed time or total kick infractions.
    """
    first_name = tg.message['reply_to_message']['from']['first_name']
    user_id = tg.message['reply_to_message']['from']['id']
    chat_id = tg.message['chat']['id']
    stepping_stones = [10800, 43200, 86400, 259200, 604800, 1209600]

    tg.database.query("SELECT COUNT(*) FROM kicks WHERE user_id={} AND chat_id={} AND active_kick=1".format(user_id,
                                                                                                            chat_id))
    query = tg.database.store_result()
    rows = query.fetch_row()
    kick_count = rows[0][0]
    try:
        kick_duration = stepping_stones[kick_count]
    except IndexError:
        kick_duration = 0
    if kick_duration <= 0:
        tg.send_message("Invalid time")
        return
    kick_time = tg.message['date']
    kicked_by = tg.message['from']['id']
    kick_reason = None
    reply_to_message_id = tg.message['reply_to_message']['message_id']
    kick = tg.kick_chat_member(user_id)
    if not kick['ok']:
        if from_warning:
            tg.send_message("{} has reached the maximum warning count but I was unable to kick them.".format(
                first_name))
        else:
            tg.send_message("It seems I'm not an admin :(")
    if kick_duration:
        if from_warning:
            kick_reason = "MAX WARNINGS"
            time_stamp = datetime.datetime.fromtimestamp(kick_time + kick_duration).strftime('%Y-%m-%d %H:%M')
            tg.send_message("{} has reached the maximum warning count. They will be unbanned on {}. "
                            "Sayonara \U0001F44B".format(first_name, time_stamp))
        else:
            if tg.message['matched_regex'] in arguments['text'][3:5]:
                kick_duration = determine_duration(tg.message['match'][0], tg.message['match'][1])
                kick_reason = tg.message['match'][2]
            elif tg.message['matched_regex'] == arguments['text'][5]:
                kick_reason = tg.message['match']
            time_stamp = datetime.datetime.fromtimestamp(kick_time + kick_duration).strftime('%Y-%m-%d %H:%M')
            tg.send_message("Successfully kicked {}. You will recieve a reminder to add them on {} (UTC)".format(
                first_name, time_stamp))
        time_id = tg.flag_time(kick_time + kick_duration)
        values = (user_id, kick_time, chat_id, kick_reason, kicked_by, time_id, reply_to_message_id, 1)
        tg.cursor.execute("INSERT INTO kicks VALUES(%s, FROM_UNIXTIME(%s), %s, %s, %s, %s, %s, %s)", values)
        tg.cursor.execute("UPDATE warnings SET active_warning=0")
    else:
        tg.send_message("{} has been permanently banned.".format(first_name))


def unban_member(tg):
    """
    Unbans a member and alerts the chat
    """
    first_name = tg.message['reply_to_message']['from']['first_name']
    tg.send_message("{}'s ban duration has ended. Please add them back.".format(first_name))
    tg.unban_chat_member(tg.message['reply_to_message']['from']['id'])


def check_message(tg):
    """
    Checks message and if user has permissions to kick
    """
    admins = tg.get_chat_administrators()
    user_id = tg.message['from']['id']
    if admins['ok']:
        admins = admins['result']
    else:
        return
    if any(user['user']['id'] == user_id for user in admins):
        if 'reply_to_message' in tg.message:
            user_id = tg.message['reply_to_message']['from']['id']
            if not any(user['user']['id'] == user_id for user in admins):
                return True
            elif user_id == tg.message['from']['id']:
                tg.send_message("You can't kick/warn yourself :(")
            else:
                tg.send_message("You can't kick/warn another admin")
        else:
            tg.send_message("This command only works by reply :(")


def determine_duration(duration, unit):
    """
    Determines how much time a user should be kicked
    """
    if 'm' in unit:
        scale = 60
    elif 'h' in unit:
        scale = 3600
    elif 'd' in unit:
        scale = 86400
    elif 'w' in unit:
        scale = 604800
    return int(float(duration) * scale)


def init_db(database):
    """
    Create warning and kick tables
    """
    cursor = database.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS warnings(user_id BIGINT NOT NULL, warning_time DATETIME NOT NULL, "
                   "chat_id BIGINT, warning_reason TEXT, warned_by BIGINT NOT NULL, reply_to_message_id BIGINT NOT "
                   "NULL, active_warning TINYINT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS kicks(user_id BIGINT NOT NULL, kick_time DATETIME NOT NULL, chat_id "
                   "BIGINT, kick_reason TEXT, kicked_by BIGINT NOT NULL, time_id VARCHAR(190), reply_to_message_id "
                   "BIGINT NOT NULL, active_kick TINYINT)")
    cursor.close()


parameters = {'name': "Admin", 'short_description': "Kick and warn chat members in your group", 'permissions': 10}

arguments = {
    'text': [
        "^/warn$", "^/warn (.*)", "^/kick$", r"/kick (\d+\.\d|\d+) ?(minutes?|mins?|hours?|days?|weeks?) ?((.*)|$)",
        r"/kick (\d+\.\d|\d+) ?([mhdw]) ?((.*)|$)", "^/kick (.*)"
    ]
}
