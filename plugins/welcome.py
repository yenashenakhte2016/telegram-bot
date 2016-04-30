def main(tg_api):
    tg_api.send_chat_action('typing')
    group = tg_api.msg['chat']['title']
    name = tg_api.msg['new_chat_participant']['first_name']
    me = tg_api.get_me()['username']
    try:
        username = tg_api.msg['new_chat_participant']['username']
    except KeyError:
        username = ""
    if me == username:
        from plugins import start
        start.main(tg_api)
    else:
        tg_api.send_message("Welcome to {}, {}!".format(group, name))


plugin_info = {
    'name': "Welcome Plugin",
    'Info': "Welcomes new members!",
    'arguments': {
        'new_chat_participant': [
            "*"
        ]
    }
}
