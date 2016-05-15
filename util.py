import re
import shutil
import requests
from db import Database
import sys
import os
import json
import logging


class ConfigUtils:
    def __init__(self, filename='config.ini', bot_name='MAIN_BOT'):
        import configparser
        self.filename = filename
        self.config = configparser.ConfigParser()
        self.config.read(filename)
        self.token = self.config[bot_name]['token']
        self.plugins = self.config[bot_name]['plugins'].split(',')
        self.sleep = float(self.config[bot_name]['sleep'])
        self.workers = int(self.config[bot_name]['workers'])

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


def clean_message(text, bot_name):  # Replace this with something based on MessageEntities
    username = "@{}".format(bot_name)
    name_match = re.search('^[!#@/]([^ ]*)({})'.format(username), text)
    if name_match:
        return text.replace(text[:name_match.end(0)], text[:name_match.end(0) - len(username)])
    else:
        return text


def name_file(file_id, file_name):
    if file_name:
        match = re.findall('(\.[0-9a-zA-Z]+$)', file_name)
        return file_id + match[0]
    else:
        return str(file_id)


def init_package(config):  # Creates the package that's passed around, replaced eventually probably
    session = requests.session()  # Creates session, used for ALL requests to telegram
    bot_info = get_me(config.token, session)  # this stores the getMe object
    database = init_db()  # Stores the database object
    plugins = init_plugins(database, config.plugins)  # Stores all plugins
    package = (('https://api.telegram.org/', 'bot{}/'.format(config.token)),  # URL [0]
               bot_info,  # bot_info [1]
               session,  # session [2]
               plugins,  # plugins [3]
               database)  # database [4]
    return package


def init_db():  # Creates the DB object and sets up hierarchy
    log = logging.getLogger(__name__)  # init log
    if not os.path.exists('data'):  # All data should be placed here
        os.makedirs('data/files')
        os.makedirs('data/logs')
    log.debug('Initializing database')
    db = Database('bot')
    log.debug('Creating plugins table')
    db.create_table('plugins', [('plugin_id', 'INT PRIMARY KEY NOT NULL'),  # Creates plugin table
                                ('plugin_name', 'TEXT'),
                                ('pretty_name', 'TEXT'),
                                ('description', 'TEXT'),
                                ('usage', 'TEXT'), ], overwrite=True)
    log.debug('Creating flagged_messages table')
    db.create_table('flagged_messages', [('plugin_id', 'INT'),  # Creates flagged messages table
                                         ('message_id', 'INT'),
                                         ('chat_id', 'INT'),
                                         ('user_id', 'INT'),
                                         ('single_use', 'BOOLEAN'),
                                         ('currently_active', 'BOOLEAN')])
    db.create_table('downloads', [('file_id', 'TEXT'), ('file_path', 'TEXT')])
    log.debug('Successfully initialized the database')
    return db


def init_plugins(db, plugin_list):
    log = logging.getLogger(__name__)  # init log
    log.info('Initializing plugins...')
    plugins = list()
    for plugin_id, plugin_name in enumerate(plugin_list):  # Read plugins from the config file
        plugin = __import__('plugins', fromlist=[plugin_name])  # Import it from the plugins folder
        plugins.append(getattr(plugin, plugin_name))  # Stores plugin objects in a dictionary
        if 'name' not in plugins[plugin_id].plugin_info:  # Check for name in plugin arguments
            log.warning('Warning: {} is missing a pretty name. Falling back to filename.'.format(plugin_name))
            plugins[plugin_id].plugin_info['name'] = plugin_name
        pretty_name = plugins[plugin_id].plugin_info['name']
        if 'desc' not in plugins[plugin_id].plugin_info:  # Check for description in plugin arguments
            log.warning('Warning: {} is missing a description.'.format(plugin_name))
            plugins[plugin_id].plugin_info['desc'] = None
        description = plugins[plugin_id].plugin_info['desc']
        if 'usage' not in plugins[plugin_id].plugin_info:  # Check for usage in plugin arguments
            log.warning('Warning: {} is missing usage.'.format(plugin_name))
            plugins[plugin_id].plugin_info['usage'] = None
        usage = json.dumps(plugins[plugin_id].plugin_info['usage'])  # Stores usage as json
        log.info('Loaded Plugin: {} - {}({}) - {} - {}'.format(plugin_id,
                                                               plugin_name,
                                                               pretty_name,
                                                               description,
                                                               usage))
        db.insert('plugins', [plugin_id, plugin_name, pretty_name, description, usage])  # Insert into DB
    log.info('Finished initializing plugins')
    return tuple(plugins)


def get_me(token, session):  # getMe
    log = logging.getLogger(__name__)  # init log
    log.info('Grabbing bot info')
    url = "https://api.telegram.org/bot{}/getMe".format(token)  # Set url for getMe
    response = fetch(url, session).json()
    if response['ok']:
        log.info('Success: {}'.format(response['result']))
        return response['result']
    else:  # Usually means the token is wrong
        log.error('Error fetching bot info\nResponse: {}\nShutting Down'.format(response))
        sys.exit()
