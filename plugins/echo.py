def main(tg):
    tg.send_chat_action('typing')
    if tg.message['flagged_message']:
        if 'text' in tg.message:
            tg.send_message(tg.message['text'])
        else:
            tg.send_message("I only echo text :(")
    elif 'reply_to_message' in tg.message:
        tg.send_message(tg.message['reply_to_message']['text'])
    elif tg.message['matched_regex'] == arguments['text'][0]:
        tg.send_message("What should I echo?", flag_message=True)
    elif tg.message['matched_regex'] == arguments['text'][1]:
        tg.send_message(tg.message['match'])


parameters = {
    'name': "Echo",
    'short_description': "The echo plugin repeats your message text",
    'long_description': "The echo plugins repeats your text back. You can use /echo alone or include text to repeat."
                        "You can also reply to a message with /echo.",
    'permissions': "01"
}

arguments = {
    'text': [
        "^/echo$",
        "^/echo (.*)"
    ]
}
