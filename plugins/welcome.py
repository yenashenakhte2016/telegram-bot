def main(tg):
    tg.send_chat_action('typing')
    group = tg.message['chat']['title']
    me = tg.get_me['result']['username']
    name = tg.message[tg.message['matched_argument']]['first_name']
    try:
        username = tg.message[tg.message['matched_argument']]['username']
    except KeyError:
        username = None
    if tg.message['matched_argument'] == 'new_chat_participant':
        if me == username:
            from plugins import start
            start.main(tg)
        else:
            tg.send_message("Welcome to {}, {}!".format(group, name))
    elif tg.message['matched_argument'] == 'left_chat_participant':
        if me != username:
            tg.send_message("Bye {} :(".format(name))


parameters = {
    'name': "Welcome",
    'short_description': "Greet new members!",
    'permissions': True
}

arguments = {
    'new_chat_participant': [
        "*"
    ],
    'left_chat_participant': [
        "*"
    ]
}
