import os
import re
import shutil
import sys

import requests

from db import Database


class ConfigUtils:
    def __init__(self, filename='config.ini'):
        import configparser
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.token = self.config['BOT_CONFIG']['token']
        self.plugins = self.config['BOT_CONFIG']['plugins'].split(',')
        self.sleep = float(self.config['BOT_CONFIG']['sleep'])
        self.workers = int(self.config['BOT_CONFIG']['workers'])
        self.admins = self.config['BOT_CONFIG']['admins'].split(',')
        if self.config['BOT_CONFIG']['extensions']:
            self.extensions = self.config['BOT_CONFIG']['extensions'].split(',')
        else:
            self.extensions = list()

    def write_config(self):
        with open(self.filename, 'w') as configfile:
            self.config.write(configfile)


def post(content, session=requests):
    response = session.post(**content)
    return response


def fetch(url, session=requests):  # Grabs from url and parses as json. note2self, don't make it parse json by default
    try:
        response = session.get(url, timeout=3)
        return response
    except requests.exceptions.ReadTimeout:
        return 'Request timed out :('
    except requests.exceptions.ConnectionError:
        return 'Unable to connect :('


def fetch_file(url, file_path, session=requests):
    response = session.get(url, stream=True)
    with open(file_path, 'wb') as out_file:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, out_file)
    return file_path


def name_file(file_id, file_name):
    if file_name:
        match = re.findall('(\.[0-9a-zA-Z]+$)', file_name)
        if match:
            return file_id + match[0]
    return str(file_id)


def init_package(config):  # Creates the package that's passed around, replaced eventually probably
    session = requests.session()  # Creates session, used for ALL requests to telegram
    bot_info = get_me(config.token, session)  # this stores the getMe object
    database = init_db()  # Stores the database object
    plugins = init_plugins(database, config.plugins)  # Stores all plugins
    misc = {
        "token": config.token, "bot_info": bot_info, "session": session, "config": config
    }
    extensions = init_extension(config.extensions)
    return [misc, plugins, database, extensions]


def init_db():  # Creates the DB object and sets up hierarchy
    if not os.path.exists('data/files'):  # All data should be placed here
        os.makedirs('data/files')
    db = Database('bot')
    db.create_table("plugins", {"plugin_name": "TEXT", "pretty_name": "TEXT", "desc": "TEXT", "permissions": "TEXT",
                                "extended_desc": "TEXT"},
                    drop_existing=True)
    db.create_table("flagged_messages", {"plugin_name": "INT", "message_id": "INT", "chat_id": "INT",
                                         "user_id": "INT", "single_use": "BOOLEAN", "currently_active": "BOOLEAN",
                                         "plugin_data": "TEXT"})
    db.create_table("flagged_time", {"plugin_name": "TEXT", "time": "INT", "plugin_data": "TEXT"})
    db.create_table("downloads", {"file_id": "TEXT", "file_path": "TEXT"})
    db.create_table("callback_queries", {"plugin_name": "INT", "data": "TEXT UNIQUE", "plugin_data": "TEXT"})
    return db


def init_plugins(db, plugin_list):
    plugin_obj_list = dict()
    plugins = __import__('plugins', fromlist=plugin_list)
    for plugin_name in plugin_list:
        try:
            plugin = getattr(plugins, plugin_name)
        except AttributeError:
            print("Failed to load {}".format(plugin_name))
            continue
        if hasattr(plugin, 'plugin_parameters'):
            if 'name' and 'desc' and 'permissions' in plugin.plugin_parameters:
                pretty_name = plugin.plugin_parameters['name']
                desc = plugin.plugin_parameters['desc']
                permissions = plugin.plugin_parameters['permissions']
                if permissions is True:
                    permissions = "11"
                elif permissions is False:
                    permissions = "00"
                elif len(permissions) > 2:
                    permissions = "11"
                else:
                    for char in permissions:
                        try:
                            int(char)
                        except ValueError:
                            permissions = '11'
                if 'extended_desc' in plugin.plugin_parameters:
                    extended_desc = plugin.plugin_parameters['extended_desc']
                else:
                    extended_desc = None
                db.insert("plugins", {"plugin_name": plugin_name, "pretty_name": pretty_name, "desc": desc,
                                      "permissions": permissions, "extended_desc": extended_desc})
                plugin_obj_list.update({plugin_name: plugin})
                print("Loaded plugin {}".format(plugin_name))
            else:
                print("{} is missing something in plugin parameters".format(plugin_name))
                continue
    return plugin_obj_list


def init_extension(extensions_list):
    extensions = dict()
    for extension_name in extensions_list:
        try:
            extension = __import__('extensions', fromlist=[extension_name])
            extensions.update({
                extension_name: {
                    'module': getattr(extension, extension_name),
                    'data': None
                }
            })
        except AttributeError:
            print("X - Unable to load extension {}".format(extension_name))
            continue
        print("Loaded extension {}".format(extension_name))
    return extensions


def get_me(token, session):  # getMe
    url = "https://api.telegram.org/bot{}/getMe".format(token)  # Set url for getMe
    response = fetch(url, session).json()
    if response['ok']:
        print("Bot: {} - @{}\n".format(response['result']['first_name'], response['result']['username']))
        return response['result']
    else:  # Usually means the token is wrong
        print('Error fetching bot info\nResponse: {}\nShutting Down'.format(response))
        sys.exit()
