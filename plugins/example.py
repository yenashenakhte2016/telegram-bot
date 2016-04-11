def main(msg):  # This is where plugin_handler will send msg
    if 'reply_to_message' in msg:
        return msg['reply_to_message']['text']
    elif type(msg['match']) is str:  # Need better way to handle this
        return "What to echo?"
    elif msg['match'][1]:
        return msg['match'][1]


plugin_info = {
    'name': "Echo Plugin",
    'Info': "Echo plugin demonstrates how plugins work!",
    'Usage': [
        "/echo",
        # "/command2",
        # "/etc"
    ]
}
regex = [
    "^[/]echo$",
    "^[/](echo) (.*)"
]