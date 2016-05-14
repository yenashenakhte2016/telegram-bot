import json
import random


def main(tg):
    tg.send_chat_action('typing')
    if tg.message['flagged_message']:
        tg.send_message(grab_plugin(tg, chance=True))
    elif tg.message['matched_regex'] == arguments['text'][0]:
        plugin_list = tg.package[4].select('pretty_name', 'plugins', return_value=True)
        message = "Here are a list of my plugins:"
        for plugin_name in plugin_list:
            message += "\n<b>• {}</b>".format(plugin_name[0])
        message += "\n\nWhich plugin do you want more info on?"
        tg.send_message(message, flag_message=True)
    elif tg.message['matched_regex'] == arguments['text'][1]:
        tg.send_message(grab_plugin(tg, match=True))


def grab_plugin(tg_api, chance=False, match=False):
    if match:
        plugin = tg_api.message['match'][1]
    else:
        plugin = tg_api.message['text']
    conditions = [('lower(pretty_name)', plugin.lower())]
    x = tg_api.package[4].select('*', 'plugins', conditions=conditions, return_value=True, single_return=True)
    if x:
        message = '<b>{}:</b>\n<pre>{}</pre>'.format(x[2], x[3])
        if x[4] != 'null':
            message += '\n<b>Usage:</b>'
            for i in json.loads(x[4]):
                message += '\n<pre>{}</pre>'.format(i)
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
