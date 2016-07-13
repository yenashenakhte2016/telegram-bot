# -*- coding: utf-8 -*-
"""
Loads plugins, extensions, and initializes the database.
"""

import os
import warnings
import configparser

import MySQLdb
import _mysql_exceptions


def master_mind():
    """Checks file path, inits config, and return plugins/extensions"""
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
    post_init(plugins.values(), database)
    post_init(extensions, database)
    database.close()
    return config, plugins, extensions


def init_database(cursor):
    """Creates various tables in the database specified in the config."""
    cursor.execute("DROP TABLE IF EXISTS plugins;")

    cursor.execute(
        "CREATE TABLE plugins(plugin_name VARCHAR(16) NOT NULL UNIQUE, pretty_name VARCHAR(16) NOT NULL "
        "UNIQUE, short_description VARCHAR(100) NOT NULL, long_description TEXT, "
        "permissions VARCHAR(2) NOT NULL, hidden TINYINT, inline_only TINYINT) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS flagged_messages(plugin_name VARCHAR(16) NOT NULL, message_id BIGINT "
        "UNSIGNED, chat_id BIGINT, user_id BIGINT UNSIGNED, currently_active BOOLEAN, single_use BOOLEAN, "
        "plugin_data TEXT) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS flagged_time(time_id VARCHAR(190) NOT NULL UNIQUE, plugin_name "
        "VARCHAR(16) NOT NULL, argument_time DATETIME NOT NULL, previous_message TEXT NOT NULL, "
        "plugin_data TEXT) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS pm_parameters(plugin_name VARCHAR(16) NOT NULL, parameter VARCHAR(164) "
        "NOT NULL, PRIMARY KEY (plugin_name, parameter)) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS downloaded_files(file_id VARCHAR(62) NOT NULL, file_path VARCHAR(100),"
        "file_hash VARCHAR(64)) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS uploaded_files(file_id VARCHAR(62) NOT NULL, file_hash VARCHAR(64),"
        "file_type VARCHAR(16)) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS inline_queries(plugin_name VARCHAR(16) NOT NULL, inline_id VARCHAR(64) "
        "NOT NULL UNIQUE) CHARACTER SET utf8mb4;")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS callback_queries(plugin_name VARCHAR(16) NOT NULL, "
        "callback_data VARCHAR(120) NOT NULL, plugin_data TEXT) CHARACTER SET utf8mb4;")

    try:
        cursor.execute(
            "CREATE UNIQUE INDEX callback_plugin_link ON callback_queries(plugin_name, callback_data)")
    except _mysql_exceptions.OperationalError:
        pass


def init_plugins(cursor):
    """
    Loads plugins given by the file_lists method. Plugins must have the parameters attribute to load. Plugins
    with no arguments dictionary are marked inline_only. All plugin info is then batch inserted into mysql.
    """
    modules = dict()
    plugin_list = file_lists('plugins')
    plugins = __import__('plugins', fromlist=plugin_list)
    values = list()

    for plugin_name in plugin_list:
        plugin = getattr(plugins, plugin_name)
        if hasattr(plugin, 'parameters'):
            pretty_name = None
            short_description = None
            long_description = None
            hidden = 0
            inline_only = 0 if hasattr(plugin, 'arguments') else 1
            if 'name' in plugin.parameters:
                pretty_name = plugin.parameters['name']
            if 'short_description' in plugin.parameters:
                short_description = plugin.parameters['short_description']
            if 'long_description' in plugin.parameters:
                long_description = plugin.parameters['long_description']
            else:
                long_description = "An extended description is not available :("
            if 'hidden' in plugin.parameters:
                hidden = plugin.parameters['hidden']
            if 'permissions' in plugin.parameters:
                permissions = numerate_permissions(plugin.parameters[
                    'permissions'])
                plugin.parameters['permissions'] = permissions
            else:
                plugin.parameters['permissions'] = permissions = '11'
            if 'inline_only' in plugin.parameters:
                inline_only = plugin.parameters['inline_only']
            values.append((plugin_name, pretty_name, short_description,
                           long_description, permissions, hidden, inline_only))
            modules.update({plugin_name: plugin})
            print("Plugin {} Loaded".format(plugin_name))

    cursor.executemany(
        "INSERT INTO plugins VALUES(%s, %s, %s, %s, %s, %s, %s);", values)
    cursor.close()

    return modules


def init_extensions():
    """Simply loads up the extensions given by the file_lists method which have the attribute main()."""
    modules = []
    extensions_list = file_lists('extensions')
    extensions = __import__('extensions', fromlist=extensions_list)

    for extension_name in extensions_list:
        extension = getattr(extensions, extension_name)
        if 'main' in dir(extension):
            modules.append(extension)
            print("Extension {} Loaded".format(extension_name))

    return modules


def post_init(modules, database):
    """
    Runs code for modules such as creating databases or fetching tokens.
    """
    for module in modules:
        if 'init_db' in dir(module):
            module.init_db(database)


def file_lists(directory):
    """Returns a list of files in a directory which end in .py (ignoring __init__.py)"""
    module_list = []

    for module in os.listdir(directory):
        if module == '__init__.py':
            continue
        elif module[-3:] == '.py':
            module_list.append(module.replace('.py', ''))
    return module_list


def numerate_permissions(permission):
    """Turns argument into standard 2 digit char"""
    if permission is True:
        permission = '11'
    elif permission is False:
        permission = '00'
    if isinstance(permission, int):
        permission = char(permission)
    return permission
