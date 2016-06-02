#!/usr/bin/python3

import json
import time
from multiprocessing import Process

import certifi
import urllib3

import bot_init
from db import Database
from route_updates import RouteMessage, route_callback_query
from tgapi import TelegramApi

base_url = 'https://api.telegram.org/'
config, plugins, extensions = bot_init.master_mind()
database = Database('bot')


http = urllib3.connection_from_url(base_url, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
token = config['BOT_CONFIG']['token']
update_id = 0

get_me = http.request('GET', "https://api.telegram.org/bot{}/getMe".format(token)).data
get_me = json.loads(get_me.decode('UTF-8'))


def main():
    global update_id

    get_update = http.request('GET',
                              "{}bot{}/getUpdates?offset={}".format(base_url, token, update_id)).data

    try:
        get_update = json.loads(get_update.decode('UTF-8'))
    except json.decoder.JSONDecodeError:
        return

    time_process = Process(target=check_time_args)
    time_process.start()

    if get_update['ok'] and get_update['result']:
        update_id = get_update['result'][-1]['update_id'] + 1

        extension_process = Process(target=run_extensions, args=(get_update['result'],))
        extension_process.daemon = True
        extension_process.start()

        for update in get_update['result']:
            if 'message' in update:
                target = RouteMessage(update['message'], plugins, database, http, get_me, config)
                message_process = Process(target=target.route_update)
                message_process.daemon = True
                message_process.start()

            elif 'callback_query' in update:
                callback_process = Process(target=route_callback_query,
                                           args=(plugins, database, get_me, config, update['callback_query']))
                callback_process.daemon = True
                callback_process.start()

    time.sleep(float(config['BOT_CONFIG']['sleep']))


def run_extensions(update):
    for module in extensions:
        module.main(update, database)


def check_time_args():
    time_args = database.select("flagged_time", ["plugin_name", "time", "plugin_data"])

    for argument in time_args:
        if argument['time'] <= time.time():
            database.delete("flagged_time", argument)
            plugin_name = argument['plugin_name']
            plugin_data = json.loads(argument['plugin_data']) if argument['plugin_data'] else None
            tg = TelegramApi(database, get_me, plugin_name, config, plugin_data=plugin_data)
            plugins[plugin_name].main(tg)


if __name__ == '__main__':
    while True:
        main()
