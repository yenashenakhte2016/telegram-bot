import concurrent.futures
import os
import re
import time

import requests

import db
import tgapi
import util


class Bot:
    def __init__(self, config):
        self.config = config
        self.misc = {
            'base_url': 'https://api.telegram.org/',
            'token': 'bot{}/'.format(self.config.token),
            'session': requests.session()
        }
        self.me = tgapi.get_me(self.misc)
        self.update_id = 0
        self.plugins = dict()
        self.bot_db = None

    def init(self):
        if not os.path.exists('data/files'):
            os.makedirs('data/files')
        self.bot_db = db.Database('bot')  # create db named bot
        self.bot_db.create_table('plugins', [('plugin_id', 'INT PRIMARY KEY NOT NULL'),  # Creates plugin table
                                             ('plugin_name', 'TEXT'),
                                             ('pretty_name', 'TEXT'),
                                             ('description', 'TEXT'),
                                             ('usage', 'TEXT')], overwrite=True)
        self.bot_db.create_table('temp_arguments', [('plugin_id', 'INT'),  # Creates table for temp arguments
                                                    ('message_id', 'INT'),
                                                    ('chat_id', 'INT'),
                                                    ('user_id', 'INT')], overwrite=True)
        for plugin_id, plugin_name in enumerate(self.config.plugins):
            plugin = __import__('plugins', fromlist=[plugin_name])
            self.plugins[plugin_name] = getattr(plugin, plugin_name)  # Stores plugin objects in a dictionary
            try:
                pretty_name = self.plugins[plugin_name].plugin_info['name']
            except KeyError:
                print('Plugin {} is missing a name.\nPlease add it to "plugin_info"'.format(plugin_name))
                self.plugins[plugin_name].plugin_info['name'] = plugin_name
                pretty_name = self.plugins[plugin_name].plugin_info['name']
            try:
                description = self.plugins[plugin_name].plugin_info['desc']
            except KeyError:
                print('Plugin {} is missing a description.\nPlease add it to "plugin_info"'.format(plugin_name))
                description = None
            try:
                usage = self.plugins[plugin_name].plugin_info['usage']
            except KeyError:
                usage = None
            self.bot_db.insert('plugins', [plugin_id, plugin_name, pretty_name, description, usage])

    def session(self, shutdown=False):
        if shutdown:
            print('Closing database connection')
            self.bot_db.db.close()
            self.bot_db.connection.commit()
            self.bot_db.connection.close()
            print('Shutting down....')
        else:
            print('Reloading bot')
            self.init()

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
                    if int(time.time()) - int(i['message']['date']) <= 180:  # Messages > 3 minutes old are ignored
                        e.submit(self.route_message, i['message'])
                    else:
                        self.check_db(i['message'])
            time.sleep(self.config.sleep)
        else:
            print('Error fetching new messages:\nCode: {}'.format(response['error_code']))
            time.sleep(self.config.sleep)

    def check_db(self, message):  # Checks if the msg is being looked for in the DB
        if 'reply_to_message' in message:
            msg_id = message['reply_to_message']['message_id']
            chat_id = message['chat']['id']
            i = self.bot_db.select(['plugin_id', 'user_id'],
                                   'temp_arguments',
                                   conditions=[('message_id', msg_id),
                                               ('chat_id', chat_id)],
                                   return_value=True, single_return=True)
            if i:
                conditions = [('plugin_id', i[0])]
                if i[1] != 'None':
                    if message['from']['id'] != i[1]:
                        return
                k = self.bot_db.select('plugin_name', 'plugins',
                                       conditions=conditions,
                                       return_value=True,
                                       single_return=True)
                if k:
                    message['from_prev_command'] = True
                    self.plugins[k[0]].main(tgapi.TelegramApi(message, self.misc, self.bot_db, k[0]))
                    self.bot_db.delete('temp_arguments', [('message_id', msg_id),
                                                          ('chat_id', chat_id),
                                                          ('plugin_id', i[0])])
                    return
        return True

    def route_message(self, message):  # Routes where plugins go
        loop = self.check_db(message)  # If the message was not previously flagged by a plugin go on as normal
        if 'text' in message:
            message['text'] = util.clean_message(message['text'], self.me['username'])
        for plugin in self.plugins:
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
                        self.plugins[plugin].main(tgapi.TelegramApi(message, self.misc, self.bot_db, plugin))
                        return True  # Return true so it flags that the msg was sent to a plugin
                    else:
                        match = re.findall(str(regex), str(built_msg))
                        if match:
                            if type(match[0]) is str:
                                message['match'] = list()
                                message['match'].append(match[0])
                            else:
                                message['match'] = match[0]
                            self.plugins[plugin].main(tgapi.TelegramApi(message, self.misc, self.bot_db, plugin))
                            return True  # Return true so it flags that the msg was sent to a plugin

                for args, nested_arg in self.plugins[plugin].plugin_info['arguments'].items():
                    if argument_loop(args, nested_arg, message):  # If a plugins wants the msg stop checking
                        loop = False
                        break
