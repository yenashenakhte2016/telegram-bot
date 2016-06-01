import configparser
import os
import concurrent.futures

from db import Database


def master_mind():
    init_database()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:
        config = e.submit(init_config).result()
        extensions = e.submit(init_extensions).result()
        plugins = e.submit(init_plugins).result()
    return config, plugins, extensions


def init_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config


def init_database():
    if not os.path.exists('data/files'):
        os.makedirs('data/files')

    database = Database('bot')

    database.create_table("plugins",
                          {"plugin_name": "TEXT", "pretty_name": "TEXT", "desc": "TEXT", "permissions": "TEXT",
                           "extended_desc": "TEXT"}, drop_existing=True)
    database.create_table("flagged_messages",
                          {"plugin_name": "INT", "message_id": "INT", "chat_id": "INT", "user_id": "INT",
                           "single_use": "BOOLEAN", "currently_active": "BOOLEAN", "plugin_data": "TEXT"})
    database.create_table("flagged_time", {"plugin_name": "TEXT", "time": "INT", "plugin_data": "TEXT"})
    database.create_table("downloads", {"file_id": "TEXT", "file_path": "TEXT"})
    database.create_table("callback_queries", {"plugin_name": "INT", "data": "TEXT UNIQUE", "plugin_data": "TEXT"})

    database.db.close()


def init_plugins():
    database = Database('bot')
    plugin_list = file_lists('plugins')

    modules = dict()
    plugins = __import__('plugins', fromlist=plugin_list)

    for plugin_name in plugin_list:
        plugin = getattr(plugins, plugin_name)

        if hasattr(plugin, 'plugin_parameters'):
            pretty_name = plugin.plugin_parameters['name']
            desc = plugin.plugin_parameters['desc']
            permissions = plugin.plugin_parameters['permissions']
            extended_desc = plugin.plugin_parameters['extended_desc'] if 'extended_desc' in plugin.plugin_parameters \
                else None
            database.insert("plugins", {'plugin_name': plugin_name, 'pretty_name': pretty_name, 'desc': desc,
                                        'extended_desc': extended_desc, 'permissions': permissions})
            modules.update({plugin_name: plugin})
            print("Plugin {} Loaded".format(plugin_name))

    database.db.close()

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
        elif '.py' in file:
            module_list.append(file.replace('.py', ''))

    return module_list
