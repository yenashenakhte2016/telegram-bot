import json


def main(tg):
    if tg.message and tg.message['matched_regex'] == arguments['text'][0]:
        tg.send_chat_action('typing')
        plugin_list = tg.database.select("plugins", ["pretty_name"])
        keyboard = []
        remaining = len(plugin_list)
        for plugin in plugin_list:
            for plugin_name in plugin.values():
                row_length = 3 if remaining >= 3 or remaining == 1 else 2
                button = {'text': plugin_name, 'callback_data': '%%help%%{}'.format(plugin_name)}
                if keyboard and len(keyboard[-1]) < row_length:
                    keyboard[-1].append(button)
                else:
                    keyboard.append([button])
                remaining -= 1
        tg.send_message("Here are a list of my functions.\nFor more detail you can use <code>/help plugin-name</code>",
                        reply_markup=tg.inline_keyboard_markup(keyboard))
    else:
        grab_plugin(tg)


def grab_plugin(tg):
    if tg.callback_query:
        plugin = tg.callback_query['data'].replace('%%help%%', '')
    else:
        plugin = tg.message['match'].lower()
    plugin_data = tg.database.select("plugins", ["pretty_name", "description", "usage"], {'pretty_name': plugin})[0]
    if tg.callback_query:
        tg.answer_callback_query(plugin_data['description'])
    else:
        tg.send_chat_action('typing')
        message = "<b>{}:</b>\n{}".format(plugin_data['pretty_name'], plugin_data['description'])
        if plugin_data['usage'] and plugin_data['usage'] != 'null':
            usage = json.loads(plugin_data['usage'])
            message += "\n<b>Usage:</b>\n"
            for command in usage:
                message += "{}\n".format(command)
        tg.send_message(message)


plugin_info = {
    'name': "Help",
    'desc': "Provides descriptions and usage for plugins you choose",
    'usage': [
        "/help"
    ],
}

arguments = {
    'text': [
        "^/help$",
        "^/help (.*)"
    ]
}
