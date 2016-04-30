def main(tg_api):  # This is where plugin_handler will send msg
    tg_api.send_chat_action('typing')
    group = tg_api.msg['chat']['title']
    name = tg_api.msg['new_chat_participant']['first_name']
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
