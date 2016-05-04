import json
import random


def main(tg_api):  # This is where plugin_handler will send msg
    tg_api.send_chat_action('typing')
    if 'from_prev_command' in tg_api.msg:
        tg_api.send_message(grab_plugin(tg_api, chance=True))
    elif len(tg_api.msg['match']) > 1:
        tg_api.send_message(grab_plugin(tg_api, match=True))
    else:
        x = tg_api.db.select('*', 'plugins', return_value=True)
        message = "Here are a list of my plugins:"
        for i in x:
            message += "\n<b>• {}</b>".format(i[2])
        message += "\n\nWhich plugin do you want more info on?"
        tg_api.send_message(message, flag_message=True)


def grab_plugin(tg_api, chance=False, match=False):
    if match:
        plugin = tg_api.msg['match'][1]
    else:
        plugin = tg_api.msg['text']
    conditions = [('lower(pretty_name)', plugin.lower())]
    x = tg_api.db.select('*', 'plugins', conditions=conditions, return_value=True, single_return=True)
    if x:
        message = '<b>{}</b><pre>{}</pre>'.format(x[2], x[3])
        if x[4] != 'None':
            message += '\n<b>Usage</b>'
            for i in json.loads(x[4]):
                message += '<pre>{}</pre>'.format(i)
        if chance:
            chance = (random.randint(1, 5))
            if chance > 3:
                message += '\n\n<b>Tip:</b> You can also use <code>/help plugin-name</code>'
    else:
        message = "I couldn't find this plugin :("
    return message


plugin_info = {
    'name': "Help",
    'desc': "Provides descriptions and usage for plugins you choose",
    'usage': [
        "/help"
    ],
}

arguments = {
    'text': [
        "^[/]help$",
        "^[/](help) (.*)"
    ]
}
