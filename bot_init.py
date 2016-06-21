# -*- coding: utf-8 -*-


import configparser
import os
import warnings

import MySQLdb
import _mysql_exceptions


def master_mind():
    warnings.filterwarnings('ignore')
    if not os.path.exists('data/files'):
        os.makedirs('data/files')
    config = configparser.ConfigParser()
    config.read('config.ini')
    database = MySQLdb.connect(**config['DATABASE'])
    init_database(database.cursor())
    plugins = init_plugins(database.cursor())
    extensions = init_extensions()
    database.commit()
    return config, plugins, extensions


def init_database(cursor):
    cursor.execute("DROP TABLE IF EXISTS plugins;")

    cursor.execute("CREATE TABLE plugins(plugin_name VARCHAR(16) NOT NULL UNIQUE, pretty_name VARCHAR(16) NOT NULL "
                   "UNIQUE, short_description VARCHAR(100) NOT NULL, long_description TEXT, "
                   "permissions VARCHAR(2) NOT NULL, hidden TINYINT, inline_only TINYINT) CHARACTER SET utf8;")

    cursor.execute("CREATE TABLE IF NOT EXISTS flagged_messages(plugin_name VARCHAR(16) NOT NULL, message_id BIGINT "
                   "UNSIGNED, chat_id BIGINT, user_id BIGINT UNSIGNED, currently_active BOOLEAN, single_use BOOLEAN, "
                   "plugin_data TEXT) CHARACTER SET utf8;")

    cursor.execute("CREATE TABLE IF NOT EXISTS flagged_time(time_id VARCHAR(248) NOT NULL UNIQUE, plugin_name "
                   "VARCHAR(16) NOT NULL, argument_time DATETIME NOT NULL, previous_message TEXT NOT NULL, "
                   "plugin_data TEXT) CHARACTER SET utf8;")

    cursor.execute("CREATE TABLE IF NOT EXISTS downloaded_files(file_id VARCHAR(62) NOT NULL, file_path VARCHAR(100),"
                   "file_hash VARCHAR(64)) CHARACTER SET utf8;")

    cursor.execute("CREATE TABLE IF NOT EXISTS uploaded_files(file_id VARCHAR(62) NOT NULL, file_hash VARCHAR(64),"
                   "file_type VARCHAR(16)) CHARACTER SET utf8;")

    cursor.execute("CREATE TABLE IF NOT EXISTS inline_queries(plugin_name VARCHAR(16) NOT NULL, inline_id VARCHAR(64) "
                   "NOT NULL UNIQUE) CHARACTER SET utf8;")

    cursor.execute("CREATE TABLE IF NOT EXISTS callback_queries(plugin_name VARCHAR(16) NOT NULL, "
                   "callback_data VARCHAR(120) NOT NULL, plugin_data TEXT) CHARACTER SET utf8;")

    try:
        cursor.execute("CREATE UNIQUE INDEX callback_plugin_link ON callback_queries(plugin_name, callback_data)")
    except _mysql_exceptions.OperationalError:
        return


def init_plugins(cursor):
    modules = dict()
    plugin_list = file_lists('plugins')
    plugins = __import__('plugins', fromlist=plugin_list)
    values = list()

    for plugin_name in plugin_list:
        plugin = getattr(plugins, plugin_name)
        if hasattr(plugin, 'parameters'):
            pretty_name = plugin.parameters['name']
            short_description = plugin.parameters['short_description']
            long_description = plugin.parameters['long_description'] if 'long_description' in plugin.parameters \
                else "An extended description is not available :("
            hidden = plugin.parameters['hidden'] if 'hidden' in plugin.parameters else 0
            if 'permissions' in plugin.parameters:
                plugin.parameters['permissions'] = permissions = numerate_permissions(plugin.parameters['permissions'])
            else:
                plugin.parameters['permissions'] = permissions = '11'
            inline_only = 0 if hasattr(plugin, 'arguments') else 1
            values.append(
                (plugin_name, pretty_name, short_description, long_description, permissions, hidden, inline_only))
            modules.update({plugin_name: plugin})
            print("Plugin {} Loaded".format(plugin_name))

    cursor.executemany("INSERT INTO plugins VALUES(%s, %s, %s, %s, %s, %s, %s);", values)
    cursor.close()

    return modules


def init_extensions():
    modules = []
    extensions_list = file_lists('extensions')
    extensions = __import__('extensions', fromlist=extensions_list)

    for extension_name in extensions_list:
        extension = getattr(extensions, extension_name)
        modules.append(extension)
        print("Extension {} Loaded".format(extension_name))

    return modules


def file_lists(directory):
    module_list = []

    for file in os.listdir(directory):
        if file == '__init__.py':
            continue
        elif '.py' == file[-3:]:
            module_list.append(file.replace('.py', ''))
    return module_list


def numerate_permissions(permission):
    if permission is True:
        permission = '11'
    elif permission is False:
        permission = '00'
    return permission
