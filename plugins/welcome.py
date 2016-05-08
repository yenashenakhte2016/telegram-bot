def main(tg_api):
    tg_api.send_chat_action('typing')
    group = tg_api.msg['chat']['title']
    me = tg_api.package[1]['username']
    name = tg_api.msg[tg_api.msg['matched_argument']]['first_name']
    try:
        username = tg_api.msg[tg_api.msg['matched_argument']]['username']
    except KeyError:
        username = ""
    if tg_api.msg['matched_argument'] == 'new_chat_participant':
        if me == username:
            from plugins import start
            start.main(tg_api)
        else:
            tg_api.send_message("Welcome to {}, {}!".format(group, name))
    elif tg_api.msg['matched_argument'] == 'left_chat_participant':
        if me == username:
            pass
        else:
            tg_api.send_message("Bye {} :(".format(name))


plugin_info = {
    'name': "Welcome",
    'desc': "Welcomes new members!",
}

arguments = {
    'new_chat_participant': [
        "*"
    ],
    'left_chat_participant': [
        "*"
    ]
}
