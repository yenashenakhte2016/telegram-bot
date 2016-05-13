def main(tg):
    tg.send_chat_action('typing')
    group = tg.message['chat']['title']
    me = tg.package[1]['username']
    name = tg.message[tg.message['matched_argument']]['first_name']
    try:
        username = tg.message[tg.message['matched_argument']]['username']
    except KeyError:
        username = ""
    if tg.message['matched_argument'] == 'new_chat_participant':
        if me == username:
            from plugins import start
            start.main(tg)
        else:
            tg.send_message("Welcome to {}, {}!".format(group, name))
    elif tg.message['matched_argument'] == 'left_chat_participant':
        if me == username:
            pass
        else:
            tg.send_message("Bye {} :(".format(name))


plugin_info = {
    'name': "Welcome",
    'desc': "Welcomes new members!"
}

arguments = {
    'new_chat_participant': [
        "*"
    ],
    'left_chat_participant': [
        "*"
    ]
}
