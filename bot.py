#!/bin/env python3

import concurrent.futures
import json
import sys
import time

import requests

from route_message import route_message
import util
from db import Database
import logging


class Bot:
    def __init__(self):
        logging.basicConfig(filename='data/logs/bot_updates.log',
                            level=logging.INFO,
                            format='%(asctime)s %(message)s',
                            datefmt='%m/%d/%Y-%I:%M:%S:')
        self.config = util.ConfigUtils()
        init_db()
        self.package = (('https://api.telegram.org/', 'bot{}/'.format(self.config.token)),  # URL
                        (self.get_me()),  # bot_info
                        (requests.session()),  # session
                        (self.init_plugins()),  # plugins
                        (Database('bot')))  # database

    def get_update(self, update_id):  # Gets new messages and sends them to route_messages
        url = "{}{}getUpdates?offset={}".format(self.package[0][0], self.package[0][1], update_id)
        response = util.fetch(url, self.package[2])
        try:
            response = response.json()
        except AttributeError:
            logging.error("Error retrieving Telegram messages\nResponse: {}".format(response))
            time.sleep(5)
            return
        if response['ok']:
            try:
                update_id = response['result'][-1]['update_id'] + 1
                logging.info('Set update ID to: {}'.format(update_id))
            except IndexError:
                time.sleep(self.config.sleep)
                return
            for i in response['result']:
                msg = i['message']
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as e:
                    if int(time.time()) - int(msg['date']) <= 180:  # Messages > 3 minutes old are ignored
                        logging.info('{} message from {}'.format(msg['chat']['type'], msg['from']['id']))
                        e.submit(route_message, msg, self.package)
                    else:
                        logging.info('OLD: {} message from {}'.format(msg['chat']['type'], msg['from']['id']))
                        e.submit(route_message, msg, self.package, check_db_only=True)
            time.sleep(self.config.sleep)
        else:
            logging.error('Error fetching Telegram messages.\nResponse: {}'.format(response))
            time.sleep(self.config.sleep)
        return update_id

    def init_plugins(self):
        logging.info('Initializing plugins')
        db = Database('bot')
        plugins = list()
        for plugin_id, plugin_name in enumerate(self.config.plugins):
            plugin = __import__('plugins', fromlist=[plugin_name])
            plugins.append(getattr(plugin, plugin_name))  # Stores plugin objects in a dictionary
            if 'name' not in plugins[plugin_id].plugin_info:
                logging.warning('Warning: {} is missing a pretty name. Falling back to filename.'.format(plugin_name))
                plugins[plugin_id].plugin_info['name'] = plugin_name
            pretty_name = plugins[plugin_id].plugin_info['name']
            if 'desc' not in plugins[plugin_id].plugin_info:
                logging.warning('Warning: {} is missing a description.'.format(plugin_name))
                plugins[plugin_id].plugin_info['desc'] = None
            description = plugins[plugin_id].plugin_info['desc']
            if 'usage' not in plugins[plugin_id].plugin_info:
                logging.warning('Warning: {} is missing usage.'.format(plugin_name))
                plugins[plugin_id].plugin_info['usage'] = None
            usage = json.dumps(plugins[plugin_id].plugin_info['usage'])
            logging.info('Loaded Plugin: {} - {}({}) - {} - {}'.format(plugin_id,
                                                                       plugin_name,
                                                                       pretty_name,
                                                                       description,
                                                                       usage))
            db.insert('plugins', [plugin_id, plugin_name, pretty_name, description, usage])
        logging.info('Finished loading plugins')
        db.db.close()
        db.connection.commit()
        db.connection.close()
        logging.info('Closed database connection')
        return tuple(plugins)

    def get_me(self):  # getMe
        logging.info('Grabbing bot info')
        url = "https://api.telegram.org/bot{}/getMe".format(self.config.token)
        response = util.fetch(url).json()
        if response['ok']:
            logging.info('Success: {}'.format(response['result']))
            return response['result']
        else:
            logging.error('Error fetching bot info\nResponse: {}'.format(response))
            logging.error('Shutting down')
            sys.exit()


def init_db():
    logging.info('Creating/Opening database')
    db = Database('bot')
    logging.info('Creating plugins table')
    db.create_table('plugins', [('plugin_id', 'INT PRIMARY KEY NOT NULL'),  # Creates plugin table
                                ('plugin_name', 'TEXT'),
                                ('pretty_name', 'TEXT'),
                                ('description', 'TEXT'),
                                ('usage', 'TEXT'), ], overwrite=True)
    logging.info('Created flagged_messages table')
    db.create_table('flagged_messages', [('plugin_id', 'INT'),  # Creates table for temp arguments
                                         ('message_id', 'INT'),
                                         ('chat_id', 'INT'),
                                         ('user_id', 'INT')])
    db.db.close()
    db.connection.commit()
    db.connection.close()
    logging.info('Successfully initialized the database')
