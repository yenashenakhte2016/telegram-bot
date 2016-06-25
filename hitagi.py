#!/usr/bin/python3
# -*- coding: utf-8 -*-


import json
import time
from multiprocessing import Process, Queue, Value
from multiprocessing.dummy import Process as ThreadProcess

import MySQLdb
import certifi
import urllib3

import bot_init
from route_updates import RouteMessage, route_callback_query, route_inline_query
from tgapi import TelegramApi

base_url = 'https://api.telegram.org/'
config, plugins, extensions = bot_init.master_mind()
sleep_time = float(config['BOT_CONFIG']['sleep'])
running = Value('i', True)
workerProcess = list()

http = urllib3.connection_from_url(base_url, cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
http.timeout = urllib3.Timeout(connect=1.0)
http.retries = 3

token = config['BOT_CONFIG']['token']
message_queue = Queue()

get_me = http.request('GET', "https://api.telegram.org/bot{}/getMe".format(token)).data
get_me = json.loads(get_me.decode('UTF-8'))
get_me.update({'date': int(time.time())})


def get_updates():
    update_id = 0
    while running.value:
        try:
            update = http.request('GET', "{}bot{}/getUpdates?offset={}".format(base_url, token, update_id))
        except urllib3.exceptions.HTTPError:
            time.sleep(sleep_time)
            continue

        if update.status == 200:
            try:
                update = json.loads(update.data.decode('UTF-8'))
            except json.decoder.JSONDecodeError:
                update = {'ok': False}
            if update['ok'] and update['result']:
                update_id = update['result'][-1]['update_id'] + 1
                for update in update['result']:
                    message_queue.put(update)
        time.sleep(sleep_time)


def process_updates():
    plugin_http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    plugin_http.timeout = urllib3.Timeout(connect=1.0)
    plugin_http.retries = 3
    database = MySQLdb.connect(**config['DATABASE'])
    cursor = database.cursor()
    update_router = RouteMessage(database, cursor, plugins, plugin_http, get_me, config)
    while running.value:
        update = message_queue.get()
        if update:
            extension_thread = ThreadProcess(target=run_extensions, args=(update,))
            extension_thread.start()
            if 'message' in update:
                update_router.route_update(update['message'])
            elif 'callback_query' in update:
                route_callback_query(database, plugins, get_me, config, plugin_http, update['callback_query'])
            elif 'inline_query' in update:
                route_inline_query(database, plugins, get_me, config, plugin_http, update['inline_query'])
            extension_thread.join()
        database.commit()
        time.sleep(sleep_time)


def run_extensions(update):
    db = MySQLdb.connect(**config['DATABASE'])
    for module in extensions:
        module.main(update, db)
        db.commit()
    db.close()


def check_time_args():
    database = MySQLdb.connect(**config['DATABASE'])
    cursor = database.cursor()
    time_arg_http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    time_arg_http.timeout = urllib3.Timeout(connect=1.0)
    time_arg_http.retries = 3

    while running.value:
        database.query("SELECT time_id, plugin_name,plugin_data,previous_message FROM flagged_time WHERE "
                       "argument_time < from_unixtime({})".format(int(time.time())))

        query = database.store_result()
        rows = query.fetch_row(how=1, maxrows=0)
        for result in rows:
            time_id = result['time_id']
            plugin_name = result['plugin_name']
            plugin_data = json.loads(result['plugin_data'])
            previous_message = json.loads(result['previous_message'])
            previous_message['time_id'] = time_id
            cursor.execute('DELETE FROM `flagged_time` WHERE time_id=%s;', (time_id,))
            tg = TelegramApi(database, get_me, plugin_name, config, time_arg_http, previous_message, plugin_data)
            plugins[plugin_name].main(tg)
        database.commit()
        time.sleep(sleep_time)
    database.close()


if __name__ == '__main__':
    getUpdatesProcess = Process(target=get_updates)
    getUpdatesProcess.start()
    for i in range(0, int(config['BOT_CONFIG']['workers'])):
        workerProcess.append(Process(target=process_updates))
        workerProcess[-1].start()
    timeArgProcess = Process(target=check_time_args)
    timeArgProcess.start()
    while running.value:
        time.sleep(5)
        for index, worker in enumerate(workerProcess):
            if not worker.is_alive():
                del workerProcess[index]
                workerProcess.append(Process(target=process_updates))
                workerProcess[-1].start()
    getUpdatesProcess.join()
    timeArgProcess.join()
    for worker in workerProcess:
        worker.join()
