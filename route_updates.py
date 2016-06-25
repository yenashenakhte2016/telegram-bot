# -*- coding: utf-8 -*-


import concurrent.futures
import json
import re
import time

import MySQLdb

from inline import InlineCallbackQuery
from inline import TelegramInlineAPI
from tgapi import TelegramApi


class RouteMessage:
    def __init__(self, database, cursor, plugins, http, get_me, config):
        self.database = database
        self.cursor = cursor
        self.plugins = plugins
        self.http = http
        self.get_me = get_me
        self.config = config
        self.message = None

    def route_update(self, message):
        self.message = message
        self.message['flagged_message'] = None
        self.message['matched_regex'] = None
        self.message['matched_argument'] = None
        self.message['cleaned_message'] = False
        self.message['pm_parameter'] = False

        if 'text' in self.message and 'entities' in self.message:
            message = self.message['text']
            bot_name = '@' + self.get_me['result']['username']
            name_match = re.search('(?i)^(/[^ ]*){}'.format(bot_name), message)
            if name_match:
                self.message['text'] = message.replace(message[:name_match.end(0)],
                                                       message[:name_match.end(0) - len(bot_name)])
                self.message['cleaned_message'] = True

        if 'reply_to_message' in self.message:
            self.check_db_reply()
        elif self.message['chat']['type'] == 'private':
            self.check_db_pm()
        else:
            self.handle_plugins()

    def check_db_reply(self):
        chat_id = self.message['chat']['id']
        message_id = self.message['reply_to_message']['message_id']
        self.database.query("SELECT plugin_name, user_id, single_use, currently_active, plugin_data "
                            "FROM flagged_messages WHERE message_id={} AND chat_id={};".format(message_id, chat_id))
        query = self.database.store_result()
        rows = query.fetch_row(how=1, maxrows=0)
        for result in rows:
            if result['user_id'] and result['user_id'] != self.message['from']['id']:
                return False
            if result['single_use']:
                self.cursor.execute("DELETE FROM flagged_messages WHERE message_id=%s",
                                    (message_id, chat_id))
            self.message['flagged_message'] = True
            plugin_data = json.loads(result['plugin_data']) if result['plugin_data'] else None
            tg = TelegramApi(self.database, self.get_me, result['plugin_name'], self.config, self.http, self.message,
                             plugin_data)
            self.plugins[result['plugin_name']].main(tg)
            self.database.commit()
        else:
            self.handle_plugins()

    def check_db_pm(self):
        chat_id = self.message['chat']['id']
        if self.handle_plugins():
            return
        self.database.query("SELECT plugin_name, single_use, message_id, plugin_data FROM flagged_messages WHERE "
                            "chat_id={} AND currently_active=1".format(chat_id))
        query = self.database.store_result()
        rows = query.fetch_row(how=1, maxrows=0) if query else list()
        for result in rows:
            message_id = result["message_id"]
            if result['single_use']:
                self.cursor.execute("DELETE FROM flagged_messages WHERE message_id=%s AND chat_id=%s",
                                    (chat_id, message_id))
            plugin_data = json.loads(result['plugin_data']) if result['plugin_data'] else None
            self.message['flagged_message'] = True
            self.cursor.execute("UPDATE flagged_messages SET currently_active=FALSE WHERE chat_id=%s", (chat_id,))
            self.database.commit()
            self.plugins[result['plugin_name']].main(
                TelegramApi(self.database, self.get_me, result['plugin_name'], self.config, self.http, self.message,
                            plugin_data))

    def handle_plugins(self):
        if int(time.time()) - int(self.message['date']) >= 180:
            return False
        chat_id = self.message['chat']['id']
        self.database.query(
            'SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_NAME="{}blacklist"'.format(chat_id))
        query = self.database.store_result()
        result = query.fetch_row()
        if not result:
            self.create_default_table()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        futures = [executor.submit(self.plugin_check, plugin) for plugin in self.plugins.items()]
        if 'text' in self.message:
            futures.append(executor.submit(self.check_pm_parameters))
        concurrent.futures.wait(futures)
        if True in [trig.result() for trig in futures]:
            return True
        else:
            return False

    def plugin_check(self, plugin):
        plugin_name, plugin_module = plugin
        if hasattr(plugin_module, 'arguments'):
            for key, value in plugin_module.arguments.items():
                if self.check_argument(key, value, self.message):
                    chat_id = self.message['chat']['id']
                    statement = 'SELECT plugin_status FROM `{}blacklist` WHERE plugin_name="{}";'.format(chat_id,
                                                                                                         plugin_name)
                    self.database.query(statement)
                    query = self.database.store_result()
                    result = query.fetch_row(how=1)
                    enabled = result[0]['plugin_status'] if result else self.add_plugin(plugin_name)
                    if enabled:
                        tg = TelegramApi(self.database, self.get_me, plugin_name, self.config, self.http, self.message)
                        plugin_module.main(tg)
                        self.database.commit()
                        return True

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

    def check_pm_parameters(self):
        match = re.findall("^/start (.*)", self.message['text'])
        if match:
            self.message['pm_parameter'] = True
            self.database.query('SELECT plugin_name FROM pm_parameters WHERE parameter="{}"'.format(match[0]))
            query = self.database.store_result()
            result = query.fetch_row()
            for plugin in result:
                tg = TelegramApi(self.database, self.get_me, plugin[0], self.config, self.http, self.message)
                self.plugins[plugin[0]].main(tg)
            return True if result else False
        return False

    def add_plugin(self, plugin_name):
        chat_name = "{}blacklist".format(self.message['chat']['id'])
        perms = self.plugins[plugin_name].parameters['permissions']
        if self.message['chat']['type'] == 'private':
            enabled = int(perms[1])
        else:
            enabled = int(perms[0])
        self.cursor.execute("INSERT INTO `{}` VALUES(%s, %s, 0000)".format(chat_name), (plugin_name, enabled))
        self.database.commit()
        return enabled

    def create_default_table(self):
        values = list()
        chat_name = "{}blacklist".format(self.message['chat']['id'])
        self.cursor.execute("CREATE TABLE `{}`(plugin_name VARCHAR(16) NOT NULL UNIQUE, "
                            "plugin_status BOOLEAN, set_by BIGINT) CHARACTER SET utf8;".format(chat_name))
        for plugin_name, module in self.plugins.items():
            perms = module.parameters['permissions']
            if self.message['chat']['type'] == 'private':
                enabled = int(perms[1])
            else:
                enabled = int(perms[0])
            values.append((plugin_name, enabled))
        self.cursor.executemany("INSERT INTO `{}` VALUES(%s, %s, 0)".format(chat_name), values)
        self.database.commit()


def route_callback_query(database, plugins, get_me, config, http, callback_query):
    data = callback_query['data']
    database.query('SELECT plugin_name, plugin_data FROM callback_queries WHERE callback_data="{}"'.format(data))
    query = database.store_result()
    rows = query.fetch_row(how=1, maxrows=0)
    for db_result in rows:
        plugin_name = db_result['plugin_name']
        plugin_data = json.loads(db_result['plugin_data']) if db_result['plugin_data'] else None
        if 'message' in callback_query:
            tg = TelegramApi(database, get_me, plugin_name, config, http, plugin_data=plugin_data,
                             callback_query=callback_query)
        else:
            tg = InlineCallbackQuery(database, config, http, callback_query)
        plugins[plugin_name].main(tg)
        database.commit()


def route_inline_query(database, plugins, get_me, config, http, inline_query):
    for plugin_name, plugin in plugins.items():
        if hasattr(plugin, 'inline_arguments'):
            for argument in plugin.inline_arguments:
                match = re.findall(str(argument), str(inline_query['query']))
                if match:
                    inline_query['matched_regex'] = argument
                    inline_query['match'] = match[0]
                    plugin.main(TelegramInlineAPI(database, get_me, plugin_name, config, http, inline_query))
                    database.commit()
                    return
