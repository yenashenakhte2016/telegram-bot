import re

import tgapi
import util


class RouteMessage:
    def __init__(self, message, package, check_db_only=False):
        self.message = message
        self.package = package
        self.message['flagged_message'] = None
        self.message['matched_regex'] = None
        self.message['matched_argument'] = None
        if self.check_db() and not check_db_only:
            self.check_plugin()

    def check_db(self):
        reply_to_message = 'reply_to_message' in self.message
        private_chat = self.message['chat']['type'] == 'private'
        if reply_to_message or private_chat:
            message_id = self.message['reply_to_message']['message_id'] if reply_to_message else None
            chat_id = self.message['chat']['id']
            db_selection = self.package[4].select(['plugin_id', 'user_id'],
                                                  'flagged_messages',
                                                  conditions=[('message_id', message_id),
                                                              ('chat_id', chat_id)],
                                                  return_value=True, single_return=True)
            if db_selection:
                self.message['flagged_message'] = True
                self.package[4].delete('flagged_messages', [('message_id', message_id), ('chat_id', chat_id)])
                self.package[3][db_selection[0]].main(tgapi.TelegramApi(self.message, self.package, db_selection[0]))
                return
        return True

    def check_plugin(self):  # Routes where plugins go
        loop = True  # If the message was not previously flagged by a plugin go on as normal
        if 'text' in self.message:
            self.message['text'] = util.clean_message(self.message['text'], self.package[1]['username'])
        for plugin_id, plugin_object in enumerate(self.package[3]):
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
                                    return check_match((k, regex), built_msg)
                    if type(values) is list:
                        for regex in values:
                            return check_match((args, regex), built_msg)
                    return

                def check_match(regex, built_msg):
                    if regex[1] is '*':
                        self.message['matched_argument'] = regex[0]
                        self.message['matched_regex'] = regex[1]
                        plugin_object.main(tgapi.TelegramApi(self.message, self.package, plugin_id))
                        return True  # Return true so it flags that the msg was sent to a plugin
                    else:
                        match = re.findall(str(regex[1]), str(built_msg))
                        if match:
                            if type(match[0]) is str:
                                self.message['match'] = list()
                                self.message['match'].append(match[0])
                            else:
                                self.message['match'] = match[0]
                            self.message['matched_argument'] = regex[0]
                            self.message['matched_regex'] = regex[1]
                            plugin_object.main(tgapi.TelegramApi(self.message, self.package, plugin_id))
                            return True  # Return true so it flags that the msg was sent to a plugin

                for args, nested_arg in plugin_object.arguments.items():
                    if argument_loop(args, nested_arg, self.message):  # If a plugins wants the msg stop checking
                        loop = False
                        break
