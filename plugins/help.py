def main(tg):
    if tg.message and tg.message['matched_regex'] == arguments['text'][0]:
        if not tg.message['cleaned_message'] and tg.message['chat']['type'] != "private":
            return
        tg.send_chat_action('typing')
        chat_id = str(tg.chat_data['chat']['id']).replace('-', '')
        plugin_list = tg.database.select("plugins", ["pretty_name", "plugin_name"])
        active_plugins = tg.database.select("chat{}blacklist".format(chat_id), ["plugin_name"], {"plugin_status": 1})
        keyboard = []
        remaining = len(plugin_list)
        for plugin in plugin_list:
            plugin_name = plugin['plugin_name']
            pretty_name = plugin['pretty_name']
            if any(plugin_name == active['plugin_name'] for active in active_plugins):
                row_length = 3 if remaining >= 3 or remaining == 1 else 2
                button = {'text': pretty_name, 'callback_data': '%%help%%{}'.format(pretty_name)}
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
        plugin = tg.callback_query['data'].replace('%%help%%', '').lower()
    else:
        plugin = tg.message['match'].lower()
    plugin_data = tg.database.select("plugins", ["pretty_name", "description", "extended_desc"],
                                     {'lower(pretty_name)': plugin})
    if plugin_data:
        plugin_data = plugin_data.pop()
        if tg.callback_query:
            tg.answer_callback_query(plugin_data['description'])
        else:
            if plugin_data['extended_desc']:
                tg.send_message(plugin_data['extended_desc'])
            else:
                tg.send_message("Extended description not available :(")
    else:
        if tg.callback_query:
            tg.answer_callback_query("Unknown error occurred")
        else:
            tg.send_message("I can't seem to find this plugin")


plugin_parameters = {
    'name': "Help",
    'desc': "Learn about this bots various functions!",
    'extended_desc': "The help plugin is self-explanatory. You can use /help to receive a list of plugins active in the"
                     "chat and /help plugin-name for an extended description.",
    'permissions': True
}

arguments = {
    'text': [
        "^/help$",
        "^/help (.*)"
    ]
}

