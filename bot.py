import requests
import util
import re
from tgapi import TelegramApi
from tgapi import get_me
import time
import concurrent.futures


class Bot:
    def __init__(self, config):
        self.config = config
        self.misc = {
            'base_url': 'https://api.telegram.org/',
            'token': 'bot{}/'.format(self.config.token),
            'session': requests.session()
        }
        self.me = get_me(self.misc)
        self.update_id = 0
        self.plugins = dict()
        self.time = int(time.time())
        for k in config.plugins:
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)

    def get_update(self):  # Gets new messages and sends them to route_messages
        url = "{}{}getUpdates?offset={}".format(self.misc['base_url'], self.misc['token'], self.update_id)
        response = util.fetch(url, self.misc['session'])
        try:
            response = response.json()
        except AttributeError:
            time.sleep(5)
            return
        if response['ok']:
            try:
                self.update_id = response['result'][-1]['update_id'] + 1
            except IndexError:
                time.sleep(self.config.sleep)
                return
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:
                for i in response['result']:
                    if self.time - int(i['message']['date']) <= 180000:
                        e.submit(self.route_message, TelegramApi(i['message'], self.misc))
            time.sleep(self.config.sleep)
        else:
            print('Error fetching new messages:\nCode: {}'.format(response['error_code']))
            time.sleep(self.config.sleep)

    def route_message(self, api_obj):  # Routes where plugins go
        loop = True
        for plugin in self.plugins:
            if loop:

                def argument_loop(arg, values, msg):  # Recursively goes through argument
                    try:
                        built_msg = msg[arg]
                    except KeyError:
                        return
                    if type(values) is dict:
                        for k, v in values.items():
                            try:
                                built_msg = built_msg[k]
                            except KeyError:
                                return
                            if type(v) is dict:
                                    argument_loop(k, v, built_msg)
                            elif type(v) is list:
                                for regex in v:
                                    match = re.findall(str(regex), str(built_msg))
                                    if match:
                                        if type(match[0]) is str:
                                            api_obj.msg['match'] = list()
                                            api_obj.msg['match'].append(match[0])
                                        else:
                                            api_obj.msg['match'] = match[0]
                                        self.plugins[plugin].main(api_obj)
                                        return True
                    if type(values) is list:
                        for regex in values:
                            match = re.findall(str(regex), str(built_msg))
                            if match:
                                if type(match[0]) is str:
                                    api_obj.msg['match'] = list()
                                    api_obj.msg['match'].append(match[0])
                                else:
                                    api_obj.msg['match'] = match[0]
                                self.plugins[plugin].main(api_obj)
                                return True
                    return

                for args, nested_arg in self.plugins[plugin].plugin_info['arguments'].items():
                    x = argument_loop(args, nested_arg, api_obj.msg)
                    if x:
                        loop = False
                        break
