#!/usr/bin/python3

import concurrent.futures
import time
import json

import util
from route_message import RouteMessage
from tgapi import TelegramApi

update_id = 0
config = util.ConfigUtils()  # Create config file object
misc, plugins, database = util.init_package(config)


def main():
    global update_id, misc, plugins, database
    url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(misc['token'], update_id)
    response = util.fetch(url, misc['session'])
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.workers)  # See docs
    time_args = database.select("flagged_time", ["plugin_id", "time", "plugin_data"])
    try:
        response = response.json()
    except (AttributeError, ValueError) as e:
        print("Error parsing Telegram response: {}\nResponse: {}".format(e, response))
        time.sleep(config.sleep)
        return
    if response['ok'] and response['result']:  # Response ok and contains results
        update_id = response['result'][-1]['update_id'] + 1
        for result in response['result']:  # Loop through result
            if 'message' in result:  # For message updates
                if_old = int(time.time()) - int(result['message']['date']) >= 180  # check if message is > 3 min old
                executor.submit(RouteMessage, result['message'], misc, plugins, database, check_db_only=if_old)
            elif 'callback_query' in result:  # For callback query updates
                db_selection = database.select("callback_queries", ["DISTINCT plugin_id", "plugin_data", "data"],
                                               {"data": result['callback_query']['data']})
                for db_result in db_selection:
                    plugin_id = db_result['plugin_id']
                    plugin_data = json.loads(db_result['plugin_data']) if db_result['plugin_data'] else None
                    api_obj = TelegramApi(misc, database, plugin_id, plugin_data=plugin_data,
                                          callback_query=result['callback_query'])
                    plugins[plugin_id].main(api_obj)
    elif not response['ok']:
        print('Response not OK\nResponse: {}'.format(response))
    for argument in time_args:  # See if any plugins want to be activated at this time
        if argument['time'] <= time.time():
            plugin_id = argument['plugin_id']
            plugin_data = json.loads(argument['plugin_data']) if argument['plugin_data'] else None
            tg = TelegramApi(misc, database, plugin_id, plugin_data=plugin_data)
            plugins[plugin_id].main(tg)
            database.delete("flagged_time", argument)
    executor.shutdown(wait=False)  # returns immediately, sub processes will close by themselves
    time.sleep(config.sleep)  # Sleep for time defined in config


if __name__ == '__main__':
    while True:
        main()
