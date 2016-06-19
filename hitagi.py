#!/usr/bin/python3
# -*- coding: utf-8 -*-


import json
import time
from multiprocessing import Process

import MySQLdb
import certifi
import urllib3

import bot_init
from route_updates import RouteMessage, route_callback_query, route_inline_query
from tgapi import TelegramApi

base_url = 'https://api.telegram.org/'
config, plugins, extensions = bot_init.master_mind()

http = urllib3.connection_from_url(base_url, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
token = config['BOT_CONFIG']['token']
update_id = 0

get_me = http.request('GET', "https://api.telegram.org/bot{}/getMe".format(token)).data
get_me = json.loads(get_me.decode('UTF-8'))
get_me.update({'date': int(time.time())})


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
        extension_process.start()

        for update in get_update['result']:
            if 'message' in update:
                target = RouteMessage(update['message'], plugins, http, get_me, config)
                message_process = Process(target=target.route_update)
                message_process.start()

            elif 'callback_query' in update:
                callback_process = Process(target=route_callback_query,
                                           args=(plugins, get_me, config, update['callback_query']))
                callback_process.start()
            elif 'inline_query' in update:
                inline_process = Process(target=route_inline_query,
                                         args=(plugins, get_me, config, update['inline_query']))
                inline_process.start()
    time_process.join()
    time.sleep(float(config['BOT_CONFIG']['sleep']))


def run_extensions(update):
    for module in extensions:
        db = MySQLdb.connect(**config['DATABASE'])
        module.main(update, db)
        db.close()


def check_time_args():
    database = MySQLdb.connect(**config['DATABASE'])
    current_time = int(time.time())
    database.query("SELECT time_id, plugin_name,plugin_data,previous_message FROM flagged_time WHERE "
                   "argument_time < from_unixtime({})".format(current_time))

    query = database.store_result()
    rows = query.fetch_row(how=1, maxrows=0)
    cursor = database.cursor() if rows else None
    for result in rows:
        time_id = result['time_id']
        plugin_name = result['plugin_name']
        plugin_data = json.loads(result['plugin_data'])
        previous_message = json.loads(result['previous_message'])
        previous_message['time_id'] = time_id
        cursor.execute('DELETE FROM `flagged_time` WHERE time_id=%s;', (time_id,))
        tg = TelegramApi(None, get_me, plugin_name, config, previous_message, plugin_data)
        plugins[plugin_name].main(tg)
    if cursor:
        cursor.close()
    database.commit()
    database.close()


if __name__ == '__main__':
    while True:
        main()
