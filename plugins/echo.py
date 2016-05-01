def main(tg_api):  # This is where plugin_handler will send msg
    tg_api.send_chat_action('typing')
    if 'from_prev_command' in tg_api.msg:
        tg_api.send_message(tg_api.msg['text'])
    elif len(tg_api.msg['match']) > 1:
        tg_api.send_message(tg_api.msg['match'][1])
    elif 'reply_to_message' in tg_api.msg:
        tg_api.send_message(tg_api.msg['reply_to_message']['text'])
    else:
        x = tg_api.send_message("What do I echo?")
        tg_api.temp_argument(message_id=x['message_id'], chat_id=x['chat']['id'])


plugin_info = {
    'name': "Echo Plugin",
    'desc': "Echo plugin demonstrates how plugins work!",
    'usage': [
        "/echo"
    ],
    'arguments': {
        'text': [
            "^[/]echo$",
            "^[/](echo) (.*)"
        ]
    }
}
