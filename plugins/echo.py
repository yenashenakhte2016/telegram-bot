def main(tg_api):  # This is where plugin_handler will send msg
    tg_api.send_chat_action('typing')
    if 'from_prev_command' in tg_api.msg:
        tg_api.send_message(tg_api.msg['text'])
    elif 'matched_regex' in tg_api.msg:
        matched_regex = tg_api.msg['matched_regex']
        regex = arguments['text']
        if matched_regex == regex[0]:
            tg_api.send_message("What do I echo?", flag_message=True, flag_user_id=True)
        else:
            tg_api.send_message(tg_api.msg['match'][1])
    elif 'reply_to_message' in tg_api.msg:
        tg_api.send_message(tg_api.msg['reply_to_message']['text'])


plugin_info = {
    'name': "Echo",
    'desc': "The echo plugin repeats your message text",
    'usage': [
        "/echo"
    ],
}

arguments = {
    'text': [
        "^[/]echo$",
        "^[/](echo) (.*)"
    ]
}
