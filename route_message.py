import re

import tgapi
import util


def route_message(message, package, check_db_only=False):
    if check_db_only:
        check_db(message, package)
    elif check_db(message, package):
        check_plugin(message, package)


def check_db(message, package):  # Checks if the msg is being looked for in the DB
    if 'reply_to_message' in message:
        msg_id = message['reply_to_message']['message_id']
        chat_id = message['chat']['id']
        i = package[4].select(['plugin_id', 'user_id'],
                              'flagged_messages',
                              conditions=[('message_id', msg_id),
                                          ('chat_id', chat_id)],
                              return_value=True, single_return=True)
        if i:
            delete_conditions = [('message_id', msg_id), ('chat_id', chat_id), ('plugin_id', i[0])]
    elif message['chat']['type'] == 'private':
        chat_id = message['chat']['id']
        i = package[4].select(['plugin_id', 'user_id'],
                              'flagged_messages',
                              conditions=[('chat_id', chat_id)],
                              return_value=True, single_return=True)
        delete_conditions = [('chat_id', chat_id)]
    else:
        return True
    if i:
        conditions = [('plugin_id', i[0])]
        if i[1]:
            if message['from']['id'] != i[1]:
                return
        k = package[4].select('plugin_id', 'plugins',
                              conditions=conditions,
                              return_value=True,
                              single_return=True)
        if k:
            message['from_prev_command'] = True
            package[3][k[0]].main(tgapi.TelegramApi(message, package, k[0]))
            package[4].delete('flagged_messages', delete_conditions)
            return
    return True


def check_plugin(message, package):  # Routes where plugins go
    loop = True  # If the message was not previously flagged by a plugin go on as normal
    if 'text' in message:
        message['text'] = util.clean_message(message['text'], package[1]['username'])
    for plugin_id, plugin_object in enumerate(package[3]):
        if loop:
            def argument_loop(arg, values, msg):  # Recursively goes through argument
                try:
                    built_msg = msg[arg]  # "increments" through message with each loop
                except KeyError:
                    return
                if type(values) is dict:
                    for k, v in values.items():
                        try:
                            built_msg = built_msg[k]
                        except KeyError:
                            return
                        if type(v) is dict:
                            argument_loop(k, v, built_msg)
                        elif type(v) is list:
                            for regex in v:
                                if check_match(regex, built_msg):
                                    return True
                if type(values) is list:
                    for regex in values:
                        if check_match(regex, built_msg):
                            return True
                return

            def check_match(regex, built_msg):
                if regex is '*':
                    plugin_object.main(tgapi.TelegramApi(message, package, plugin_id))
                    return True  # Return true so it flags that the msg was sent to a plugin
                else:
                    match = re.findall(str(regex), str(built_msg))
                    if match:
                        if type(match[0]) is str:
                            message['match'] = list()
                            message['match'].append(match[0])
                        else:
                            message['match'] = match[0]
                        message['matched_regex'] = regex
                        plugin_object.main(tgapi.TelegramApi(message, package, plugin_id))
                        return True  # Return true so it flags that the msg was sent to a plugin

            for args, nested_arg in plugin_object.arguments.items():
                if argument_loop(args, nested_arg, message):  # If a plugins wants the msg stop checking
                    loop = False
                    break
