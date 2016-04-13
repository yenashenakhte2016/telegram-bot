def main(msg):  # This is where plugin_handler will send msg
    if 'reply_to_message' in msg:
        print(msg)
        return msg['reply_to_message']['text']
    try:
        if msg['match'][1]:  # Need better way to handle this
            return msg['match'][1]
    except IndexError:
        if msg['match'][0]:
            return "What do I echo?"


plugin_info = {
    'name': "Echo Plugin",
    'Info': "Echo plugin demonstrates how plugins work!",
    'Usage': [
        "/echo",
        # "/command2",
        # "/etc"
    ]
}
arguments = {
    'type': ['text'],
    'global_regex': [
        "^[/]echo$",
        "^[/](echo) (.*)"
    ]
}
