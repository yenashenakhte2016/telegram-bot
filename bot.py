import requests
import util
import re
from tgapi import TelegramApi
from tgapi import get_me
import time
import sys
from multiprocessing.dummy import Pool


class Bot:
    def __init__(self, config):
        self.config = config
        self.misc = {
            'base_url': 'https://api.telegram.org/',
            'token': 'bot{}/'.format(self.config.token),
            'session': requests.session()
        }
        try:
            self.me = get_me(self.misc)
        except AttributeError:
            util.timeout('Telegram')
        self.update_id = 0
        self.plugins = dict()
        self.loop = dict()
        self.time = int(time.time())
        for k in config.plugins:
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)
        self.process_plugins()

    def get_update(self):  # Gets new messages and sends them to plugin_handler
        url = "{}{}getUpdates?offset={}".format(self.misc['base_url'], self.misc['token'], self.update_id)
        response = util.fetch(url, self.misc['session'])
        try:
            response = response.json()
        except AttributeError:
            print("Can't connect to Telegram servers :(")
            util.timeout('Telegram')
            return None
        if response['ok']:
            pool = Pool()
            pool.map(self.route_message, response['result'])
            pool.close()
            pool.join()
            time.sleep(self.config.sleep)
        else:
            print("There seems to be something wrong with your token")
            print("Shutting down....")
            sys.exit()

    def route_message(self, msg):  # Checks if a plugin wants this message type then sends to relevant class
        api_obj = TelegramApi(msg['message'], self.misc)
        if msg['update_id'] >= self.update_id:
            self.update_id = api_obj.msg['update_id'] + 1  # Updates update_id's value
        msg = None
        if self.time - int(api_obj.msg['date']) <= 180000:
            for k in self.loop:
                if k in api_obj.msg:
                    getattr(self, 'process_{}'.format(k))(api_obj)

    def process_plugins(self):
        for p in self.plugins:
            for v in self.plugins[p].arguments['type']:
                try:
                    self.loop[v].append(p)
                except KeyError:
                    self.loop[v] = list()
                    self.loop[v].append(p)

    def process_text(self, api_obj):
        api_obj.msg['text'] = util.clean_message(api_obj.msg['text'], self.me)
        for x in self.loop['text']:
            for regex in self.plugins[x].arguments['global_regex']:
                match = re.findall(regex, api_obj.msg['text'])
                if match:
                    if type(match[0]) is str:
                        api_obj.msg['match'] = list()
                        api_obj.msg['match'].append(match[0])
                    else:
                        api_obj.msg['match'] = match[0]
                    self.plugins[x].main(api_obj)

    def process_document(self, api_obj):
        all_plugin = None
        for x in self.loop['document']:
            try:
                for mime_type in self.plugins[x].arguments['mime_type']:
                    if 'all' in mime_type:
                        all_plugin = x
                    elif mime_type in api_obj.msg['document']['mime_type']:
                        api_obj.msg['local_file_path'] = api_obj.get_file(api_obj.msg['document']['file_id'],
                                                                          download=True)
                        if api_obj.msg['local_file_path']:
                            self.plugins[x].main(api_obj)
                            break
            except KeyError:
                print('Plugin "{}" is missing mime_type argument. Will be disabled.'.format(x))
                self.loop['document'].remove(x)
        if all_plugin:
            api_obj.msg['local_file_path'] = api_obj.get_file(api_obj.msg['document']['file_id'], download=True)
            if api_obj.msg['local_file_path']:
                self.plugins[all_plugin].main(api_obj)
