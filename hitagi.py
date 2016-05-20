#!/usr/bin/python3

import concurrent.futures
import time

import util
from route_message import RouteMessage

update_id = 0
config = util.ConfigUtils()  # Create config file object
misc, plugins, database = util.init_package(config)


def main():
    global update_id, misc, plugins, database
    url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(misc['token'], update_id)
    response = util.fetch(url, misc['session'])
    try:
        response = response.json()
    except AttributeError:
        print("Error parsing Telegram response\nResponse: {}".format(response))
        time.sleep(5)
        return
    if response['ok'] and response['result']:  # Response ok and contains results
        update_id = response['result'][-1]['update_id'] + 1
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.workers)  # See docs
        for result in response['result']:  # Loop through result
            if_old = int(time.time()) - int(result['message']['date']) >= 180  # check if message is older than 3 min
            executor.submit(RouteMessage, result['message'], misc, plugins, database, check_db_only=if_old)
        executor.shutdown(wait=False)  # returns immediately, sub processes will close by themselves
    elif not response['ok']:  # Response not ok
        print('Response not OK\nResponse: {}'.format(response))
    time.sleep(config.sleep)  # Sleep for time defined in config


if __name__ == '__main__':
    while True:
        main()
