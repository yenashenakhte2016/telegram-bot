#!/usr/bin/python3

import concurrent.futures
import logging
import time

import util
from route_message import RouteMessage

update_id = 0
config = util.ConfigUtils()  # Create config file object
package = util.init_package(config)
log = logging.getLogger(__name__)  # init log


def main():
    global update_id
    url = "{}{}getUpdates?offset={}".format(package[0][0], package[0][1], update_id)
    response = util.fetch(url, package[2])
    try:
        response = response.json()
    except AttributeError:
        log.error("Error parsing Telegram response\nResponse: {}".format(response))
        time.sleep(5)
        return
    if response['ok'] and response['result']:  # Response ok and contains results
        update_id = response['result'][-1]['update_id'] + 1
        log.debug("Set update_id to {}".format(update_id))
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.workers)  # See docs
        for result in response['result']:  # Loop through result
            if_old = int(time.time()) - int(result['message']['date']) >= 180  # check if message is older than 3 min
            log.debug("Routing message {} - Old: {}".format(result['message']['message_id'], if_old))
            executor.submit(RouteMessage, result['message'], package, check_db_only=if_old)  # submit to executor
        executor.shutdown(wait=False)  # returns immediately, sub processes will close by themselves
    elif not response['ok']:  # Response not ok
        log.error('Response not OK\nResponse: {}'.format(response))
    time.sleep(config.sleep)  # Sleep for time defined in config


if __name__ == '__main__':
    while True:
        main()
