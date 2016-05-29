import json
import re
import time
from sqlite3 import OperationalError

from tgapi import TelegramApi


class RouteMessage:
    def __init__(self, message, misc, plugins, database):
        self.message = message
        self.misc = misc
        self.plugins = plugins
        self.database = database
        self.message['flagged_message'] = None
        self.message['matched_regex'] = None
        self.message['matched_argument'] = None
        self.message['cleaned_message'] = False

    def route_update(self):
        if 'text' in self.message and 'entities' in self.message:
            message = self.message['text']
            bot_name = '@' + self.misc['bot_info']['username']
            name_match = re.search('^(/[^ ]*){}'.format(bot_name), message)
            if name_match:
                self.message['text'] = message.replace(message[:name_match.end(0)],
                                                       message[:name_match.end(0) - len(bot_name)])
                self.message['cleaned_message'] = True
        if 'reply_to_message' in self.message and not self.check_db_reply():
            self.plugin_check()
        elif self.message['chat']['type'] == 'private':
            self.check_db_pm()
        else:
            self.plugin_check()

    def check_db_reply(self):
        chat_id = self.message['chat']['id']
        message_id = self.message['reply_to_message']['message_id']
        db_selection = self.database.select("flagged_messages",
                                            ["DISTINCT plugin_name", "user_id", "single_use", "currently_active",
                                             "plugin_data"],
                                            {"message_id": message_id, "chat_id": chat_id})
        if db_selection:
            for result in db_selection:
                if result['user_id'] and result['user_id'] != self.message['from']['id']:
                    return True
                if result['single_use']:
                    self.database.delete('flagged_messages', {'message_id': message_id, 'chat_id': chat_id})
                self.message['flagged_message'] = True
                if result['plugin_data']:
                    plugin_data = json.loads(result['plugin_data'])
                else:
                    plugin_data = None
                self.plugins[result['plugin_name']].main(
                    TelegramApi(self.misc, self.database, result['plugin_name'], self.message, plugin_data))
            return True

    def check_db_pm(self):
        chat_id = self.message['chat']['id']
        if self.plugin_check():
            return
        db_selection = self.database.select("flagged_messages",
                                            ["DISTINCT plugin_name", "single_use", "message_id", "plugin_data"],
                                            {"chat_id": chat_id, "currently_active": True})
        if db_selection:
            for result in db_selection:
                message_id = result["message_id"]
                if result['single_use']:
                    self.database.delete('flagged_messages', {'message_id': message_id, 'chat_id': chat_id})
                if result['plugin_data']:
                    plugin_data = json.loads(result['plugin_data'])
                else:
                    plugin_data = None
                self.message['flagged_message'] = True
                self.database.update("flagged_messages", {"currently_active": False},
                                     {"chat_id": chat_id})
                self.plugins[result['plugin_name']].main(
                    TelegramApi(self.misc, self.database, result['plugin_name'], self.message, plugin_data)
                )

    def plugin_check(self):
        if int(time.time()) - int(self.message['date']) >= 180:
            return False
        plugin_triggered = False
        for plugin_name, plugin_module in self.plugins.items():
            for key, value in plugin_module.arguments.items():
                if self.check_argument(key, value, self.message):
                    chat_id = str(self.message['chat']['id']).replace('-', '')
                    try:
                        db_selection = self.database.select("chat{}blacklist".format(chat_id), ["plugin_status"],
                                                            {"plugin_name": plugin_name})
                    except OperationalError:
                        self.create_default_table()
                        db_selection = self.database.select("chat{}blacklist".format(chat_id), ["plugin_status"],
                                                            {"plugin_name": plugin_name})
                    if db_selection:
                        enabled = db_selection[0]['plugin_status']
                    else:
                        enabled = self.add_plugin(plugin_name)
                    if enabled == 1:
                        plugin_triggered = True
                        plugin_module.main(TelegramApi(self.misc, self.database, plugin_name, self.message))
        return plugin_triggered

    def check_argument(self, key, value, incremented_message):
        if key in incremented_message:
            if type(value) is list:
                incremented_message = incremented_message[key]
                return self.check_match(key, value, incremented_message)
            elif type(value) is dict:
                incremented_message = incremented_message[key]
                for key1, value1 in value.items():
                    if self.check_argument(key1, value1, incremented_message):
                        return True
        else:
            return False

    def check_match(self, key, values, incremented_message):
        self.message['matched_argument'] = key
        if '*' in values:
            self.message['matched_regex'] = '*'
            return True
        for regex in values:
            match = re.findall(str(regex), str(incremented_message))
            if match:
                self.message['matched_regex'] = regex
                self.message['match'] = match[0]
                return True
        return False

    def add_plugin(self, plugin_name):
        chat_name = "chat{}blacklist".format(self.message['chat']['id']).replace('-', '')
        select = self.database.select("plugins", ["permissions"], {"plugin_name": plugin_name})
        perms = select[0]['permissions']
        if self.message['chat']['type'] == 'private':
            enabled = int(perms[1])
        else:
            enabled = int(perms[0])
        self.database.insert(chat_name, {"plugin_name": plugin_name, "plugin_status": enabled})
        return enabled

    def create_default_table(self):
        chat_name = "chat{}blacklist".format(self.message['chat']['id']).replace('-', '')
        self.database.create_table(chat_name, {'plugin_name': 'TEXT UNIQUE', "plugin_status": "INT"})
        for plugin_name, module in self.plugins.items():
            perms = self.database.select("plugins", ["permissions"], {"plugin_name": plugin_name})
            enabled = perms[0]['permissions']
            if self.message['chat']['type'] == 'private':
                enabled = int(enabled[1])
            else:
                enabled = int(enabled[0])
            self.database.insert(chat_name, {"plugin_name": plugin_name, "plugin_status": enabled})


def route_callback_query(callback_query, database, plugins, misc):
    db_selection = database.select("callback_queries", ["DISTINCT plugin_name", "plugin_data", "data"],
                                   {"data": callback_query['data']})
    for db_result in db_selection:
        plugin_name = db_result['plugin_name']
        plugin_data = json.loads(db_result['plugin_data']) if db_result['plugin_data'] else None
        api_obj = TelegramApi(misc, database, plugin_name, plugin_data=plugin_data,
                              callback_query=callback_query)
        plugins[plugin_name].main(api_obj)
