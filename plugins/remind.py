import random


def main(tg):
    tg.send_chat_action('typing')
    if tg.plugin_data:
        tg.send_message("Reminder:\n{}".format(tg.plugin_data['message']))
    elif tg.message['matched_regex']:
        response_time = tg.message['match'][1]
        unit = tg.message['match'][2]
        message = tg.message['match'][3]
        current_time = tg.message['date']
        package, message = add_entry(response_time, unit, message, current_time)
        tg.flag_time(**package)
        tg.send_message(message)


def add_entry(response_time, unit, message, time):
    if message[0:3] == 'to ':
        message = message[3:]
    responses = ["Ok, I will remind you in", "I'll be sure to remind you in", "Expect to hear from me in",
                 "I'll be sure to ping you in"]
    response_time = int(response_time)
    epoch_time = 0
    response = "{} {} ".format(random.choice(responses), response_time)
    if unit.lower() == 's' or 'second' in unit:
        epoch_time = response_time
        response += 'second'
    elif unit.lower() == 'm' or 'minute' in unit:
        epoch_time = response_time * 60
        response += 'minute'
    elif unit.lower() == 'h' or 'hour' in unit:
        epoch_time = response_time * 60 * 60
        response += 'hour'
    if response_time > 1:
        response += 's'
    time += epoch_time
    package = {
        'time': time,
        'plugin_data': {
            'message': message
        }
    }
    return [package, response]


plugin_parameters = {
    'name': "Remind",
    'desc': "The remind plugin gives you a notification at the time you specify",
    'extended_desc': "The remind plugins pings you at a time you specify. To cancel the reminder you just have to "
                     "delete the message which triggered it. Here's an example: \n<code>Remind me in 30 minutes to take"
                     " out the trash</code>",
    'permissions': True
}

arguments = {
    'text': [
        "(?i)(remind) .* (\d+)([smd]) (.*)",
        "(?i)(remind) .* (\d+) (seconds|minutes|hours) (.*)",
        "(?i)(remind) .* (\d+) (second|minute|hour) (.*)",
    ]
}
