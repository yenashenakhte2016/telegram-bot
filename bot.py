import concurrent.futures
import os
import re
import time

import requests

import db
import util
from tgapi import TelegramApi
from tgapi import get_me


class Bot:
    def __init__(self, config):
        self.config = config
        self.misc = {
            'base_url': 'https://api.telegram.org/',
            'token': 'bot{}/'.format(self.config.token),
            'session': requests.session()
        }
        self.me = get_me(self.misc)
        self.update_id = 0
        self.plugins = dict()
        self.bot_db = None

    def init(self):
        if not os.path.exists('data/files'):
            os.makedirs('data/files')
        self.bot_db = db.Database('bot')
        self.bot_db.execute('DROP TABLE IF EXISTS plugins')
        self.bot_db.execute("""CREATE TABLE plugins (
        plugin_id INT PRIMARY KEY NOT NULL,
        plugin_name TEXT,
        pretty_name TEXT,
        description TEXT,
        usage TEXT)""")
        self.bot_db.execute("""CREATE TABLE temp_arguments (
            plugin_id INT,
            message_id INT,
            chat_id INT)""")
        for plugin_id, plugin_name in enumerate(self.config.plugins):
            plugin = __import__('plugins', fromlist=[plugin_name])
            self.plugins[plugin_name] = getattr(plugin, plugin_name)
            try:
                pretty_name = self.plugins[plugin_name].plugin_info['name']
            except KeyError:
                print('Plugin {} is missing a name.\nPlease add it to "plugin_info"'.format(plugin))
                self.plugins[plugin_name].plugin_info['name'] = plugin_name
                pretty_name = self.plugins[plugin_name].plugin_info['name']
            try:
                description = self.plugins[plugin_name].plugin_info['desc']
            except KeyError:
                print('Plugin {} is missing a description.\nPlease add it to "plugin_info"'.format(plugin))
                description = None
            try:
                usage = self.plugins[plugin_name].plugin_info['usage']
            except KeyError:
                usage = None
            self.bot_db.execute('insert into plugins values({},"{}","{}","{}","{}")'.format
                                (plugin_id, plugin_name, pretty_name, description, usage))

    def get_update(self):  # Gets new messages and sends them to route_messages
        url = "{}{}getUpdates?offset={}".format(self.misc['base_url'], self.misc['token'], self.update_id)
        response = util.fetch(url, self.misc['session'])
        try:
            response = response.json()
        except AttributeError:
            time.sleep(5)
            return
        if response['ok']:
            try:
                self.update_id = response['result'][-1]['update_id'] + 1
            except IndexError:
                time.sleep(self.config.sleep)
                return
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as e:
                for i in response['result']:
                    if int(time.time()) - int(i['message']['date']) <= 180:
                        e.submit(self.route_message, i['message'])

            time.sleep(self.config.sleep)
        else:
            print('Error fetching new messages:\nCode: {}'.format(response['error_code']))
            time.sleep(self.config.sleep)

    def check_db(self, message):
        if 'reply_to_message' in message:
            msg_id = message['reply_to_message']['message_id']
            chat_id = message['chat']['id']
            self.bot_db.execute('SELECT plugin_id FROM temp_arguments where message_id={} AND chat_id={}'.format
                                (msg_id, chat_id))
            for i in self.bot_db.db:
                if i[0]:
                    self.bot_db.execute('SELECT plugin_name FROM plugins where plugin_id={}'.format
                                        (i[0]))
                    for k in self.bot_db.db:
                        message['from_prev_command'] = True
                        self.plugins[k[0]].main(TelegramApi(message, self.misc, self.bot_db, k[0]))
                        self.bot_db.execute("""DELETE FROM temp_arguments
WHERE message_id={} AND chat_id={} AND plugin_id={};""".format(msg_id, chat_id, i[0]))
        return True

    def route_message(self, message):  # Routes where plugins go
        loop = self.check_db(message)
        if loop:
            if 'text' in message:
                message['text'] = util.clean_message(message['text'], self.me['username'])
            for plugin in self.plugins:

                def argument_loop(arg, values, msg):  # Recursively goes through argument
                    try:
                        built_msg = msg[arg]
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
                        self.plugins[plugin].main(TelegramApi(message, self.misc, self.bot_db, plugin))
                        return True
                    else:
                        match = re.findall(str(regex), str(built_msg))
                        if match:
                            if type(match[0]) is str:
                                message['match'] = list()
                                message['match'].append(match[0])
                            else:
                                message['match'] = match[0]
                            self.plugins[plugin].main(TelegramApi(message, self.misc, self.bot_db, plugin))
                            return True

                for args, nested_arg in self.plugins[plugin].plugin_info['arguments'].items():
                    x = argument_loop(args, nested_arg, message)
                    if x:
                        loop = False
                        break
