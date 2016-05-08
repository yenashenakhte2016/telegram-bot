#!/bin/env python3

import concurrent.futures
import json
import sys
import time

import requests

from route_message import route_message
import util
from db import Database


class Bot:
    def __init__(self):
        self.config = util.ConfigUtils()
        init_db()
        self.package = (('https://api.telegram.org/', 'bot{}/'.format(self.config.token)),  # URL
                        (get_me(self.config.token)),  # bot_info
                        (requests.session()),  # session
                        (init_plugins(self.config.plugins)),  # plugins
                        (Database('bot')))  # database

    def get_update(self, update_id):  # Gets new messages and sends them to route_messages
        url = "{}{}getUpdates?offset={}".format(self.package[0][0], self.package[0][1], update_id)
        response = util.fetch(url, self.package[2])
        try:
            response = response.json()
        except AttributeError:
            time.sleep(5)
            return update_id
        if response['ok']:
            try:
                update_id = response['result'][-1]['update_id'] + 1
            except IndexError:
                time.sleep(self.config.sleep)
                return update_id
            for i in response['result']:
                if int(time.time()) - int(i['message']['date']) <= 180:  # Messages > 3 minutes old are ignored
                    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as e:
                        e.submit(route_message, i['message'], self.package)
                else:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as e:
                        e.submit(route_message, i['message'], self.package, check_db_only=True)
            time.sleep(self.config.sleep)
        else:
            print('Error fetching new messages:\nCode: {}'.format(response['error_code']))
            time.sleep(self.config.sleep)
        return update_id


def init_db():
    db = Database('bot')
    db.create_table('plugins', [('plugin_id', 'INT PRIMARY KEY NOT NULL'),  # Creates plugin table
                                ('plugin_name', 'TEXT'),
                                ('pretty_name', 'TEXT'),
                                ('description', 'TEXT'),
                                ('usage', 'TEXT')], overwrite=True)
    db.create_table('flagged_messages', [('plugin_id', 'INT'),  # Creates table for temp arguments
                                         ('message_id', 'INT'),
                                         ('chat_id', 'INT'),
                                         ('user_id', 'INT')])
    db.db.close()
    db.connection.commit()
    db.connection.close()


def init_plugins(plugins_list):
    db = Database('bot')
    plugins = list()
    for plugin_id, plugin_name in enumerate(plugins_list):
        plugin = __import__('plugins', fromlist=[plugin_name])
        plugins.append(getattr(plugin, plugin_name))  # Stores plugin objects in a dictionary
        if 'name' not in plugins[plugin_id].plugin_info:
            print('Warning: {} is missing a pretty name. Falling back to filename.'.format(plugin_name))
            plugins[plugin_id].plugin_info['name'] = plugin_name
        pretty_name = plugins[plugin_id].plugin_info['name']
        if 'desc' not in plugins[plugin_id].plugin_info:
            print('Warning: {} is missing a description.'.format(plugin_name))
            plugins[plugin_id].plugin_info['desc'] = None
        description = plugins[plugin_id].plugin_info['desc']
        if 'usage' not in plugins[plugin_id].plugin_info:
            print('Warning: {} is missing usage.'.format(plugin_name))
            plugins[plugin_id].plugin_info['usage'] = None
        usage = json.dumps(plugins[plugin_id].plugin_info['usage'])
        db.insert('plugins', [plugin_id, plugin_name, pretty_name, description, usage])
    db.db.close()
    db.connection.commit()
    db.connection.close()
    return tuple(plugins)


def get_me(token):  # getMe
    url = "https://api.telegram.org/bot{}/getMe".format(token)
    response = util.fetch(url).json()
    if response['ok']:
        return response['result']
    else:
        print("There seems to be an error :(\nCheck your token and connection to the internet")
        print(response)
        sys.exit()
