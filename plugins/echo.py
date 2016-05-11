def main(tg_api):  # This is where plugin_handler will send msg
    tg_api.send_chat_action('typing')
    if tg_api.msg['flagged_message']:
        tg_api.send_message(tg_api.msg['text'])
    elif 'reply_to_message' in tg_api.msg:
        tg_api.send_message(tg_api.msg['reply_to_message']['text'])
    elif tg_api.msg['matched_regex'] == arguments['text'][0]:
        tg_api.send_message("What do I echo?", flag_message=True, flag_user_id=True)
    elif tg_api.msg['matched_regex'] == arguments['text'][1]:
        tg_api.send_message(tg_api.msg['match'][1])


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
