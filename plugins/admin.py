on = '🔵'
off = '🔴'
admin = '⚪️'
chat_id = int
tg = None


def main(tg_api):
    global chat_id, tg
    tg = tg_api
    chat_id = str(tg.chat_data['chat']['id']).replace('-', '')
    if tg.callback_query:
        answer_callback()
    else:
        tg.send_chat_action('typing')
        if tg.message['chat']['type'] != 'private':
            keyboard = create_plugin_keyboard()
            tg.send_message("Here are a list of plugins and their status. Only group admins and mods can toggle these.",
                            reply_markup=tg.inline_keyboard_markup(keyboard))
        else:
            tg.send_message("You can only toggle plugins in groups!")


def answer_callback():
    plugin = tg.callback_query['data'].replace('%%toggle%%', '')
    if plugin == tg.plugin_name:
        tg.answer_callback_query("You can't disable this plugin!")
        return
    updated = update_plugin_status(plugin)
    if updated:
        tg.answer_callback_query("Toggled the plugin status!")
        keyboard = create_plugin_keyboard()
        tg.edit_message_reply_markup(message_id=tg.callback_query['message']['message_id'],
                                     reply_markup=tg.inline_keyboard_markup(keyboard))
    elif updated is False:
        tg.answer_callback_query("Only bot admins can toggle this plugin!")
    else:
        tg.answer_callback_query("Only chat mods can toggle this plugin!")


def update_plugin_status(plugin_name):
    chat = "chat{}blacklist".format(chat_id)
    plugin = tg.database.select("chat{}blacklist".format(chat_id), ["plugin_status"], {'plugin_name': plugin_name})[0]
    if plugin['plugin_status'] != 2:
        has_permission = check_if_mod()
        if not has_permission:
            return
    else:
        has_permission = check_if_admin()
        if not has_permission:
            return False
    new_status = 0 if plugin['plugin_status'] == 1 else 1
    tg.database.update(chat, {"plugin_status": new_status}, {"plugin_name": plugin_name})
    return True


def create_plugin_keyboard():
    keyboard = list()
    plugin_status = fetch_plugin_status()
    plugin_list = tg.database.select("plugins", ["plugin_name", "pretty_name", "permissions"])
    remaining = len(plugin_list)

    for plugin in plugin_list:
        plugin_name = plugin['plugin_name']
        pretty_plugin_name = plugin['pretty_name']
        permissions = plugin['permissions']
        button = {'callback_data': "%%toggle%%{}".format(plugin_name), 'text': "{} - {}"}

        if plugin_name == tg.plugin_name:
            continue

        if plugin_name not in plugin_status:
            chat_name = "chat{}blacklist".format(chat_id)

            if tg.chat_data['chat']['type'] == "private":
                status = permissions[1]
            else:
                status = permissions[0]
            tg.database.insert(chat_name, {"plugin_name": plugin_name, "plugin_status": status})
        else:
            status = plugin_status[plugin_name]

        if status == 0:
            button['text'] = button['text'].format(off, pretty_plugin_name)
        elif status == 1:
            button['text'] = button['text'].format(on, pretty_plugin_name)
        elif status == 2:
            button['text'] = button['text'].format(admin, pretty_plugin_name)

        remaining -= 1
        row_length = 3 if remaining >= 3 or remaining == 1 else 2
        if keyboard and len(keyboard[-1]) < row_length:
            keyboard[-1].append(button)
        else:
            keyboard.append([button])
    return keyboard


def fetch_plugin_status():
    plugin_status = dict()
    db_selection = tg.database.select("chat{}blacklist".format(chat_id), ["plugin_name", "plugin_status"])
    for result in db_selection:
        plugin_status[result['plugin_name']] = result['plugin_status']
    return plugin_status


def check_if_mod():
    admins = tg.get_chat_administrators()
    user_id = tg.callback_query['from']['id']
    if admins['ok']:
        admins = admins['result']
    else:
        return
    if any(user['user']['id'] == user_id for user in admins):
        return True


def check_if_admin():
    user_id = str(tg.callback_query['from']['id'])
    if user_id in tg.config['BOT_CONFIG']['admins']:
        return True
    return


plugin_parameters = {
    'name': "Administration",
    'desc': "Enable and disable plugins in your group!",
    'extended_desc': "The administration plugin allows moderators (and only moderators) to enable or disable plugins "
                     "in their groups. You can use /admin to display a list of plugins and their status. "
                     "Plugins which have a white circle will need to be enabled by the bot admin.",
    'permissions': True
}

arguments = {
    'text': [
        "^/admin$"
    ]
}
