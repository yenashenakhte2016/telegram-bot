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
                    e.submit(self.route_message, TelegramApi(i['message'], self.misc))
            time.sleep(self.config.sleep)
        else:
            print('Error fetching new messages:\nCode: {}'.format(response['error_code']))

    def route_message(self, api_obj):  # Checks if a plugin wants this message type then sends to relevant class
        if self.time - int(api_obj.msg['date']) <= 180000:
            for k in self.loop:
                if k in api_obj.msg:
                    getattr(self, 'process_{}'.format(k))(api_obj)

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
            for mime_type in self.plugins[x].arguments['mime_type']:
                if 'all' in mime_type:
                    all_plugin = x
                elif mime_type in api_obj.msg['document']['mime_type']:
                    api_obj.msg['local_file_path'] = api_obj.get_file(api_obj.msg['document']['file_id'], download=True)
                    if api_obj.msg['local_file_path']:
                        self.plugins[x].main(api_obj)
                        break
        if all_plugin:
            api_obj.msg['local_file_path'] = api_obj.get_file(api_obj.msg['document']['file_id'], download=True)
            if api_obj.msg['local_file_path']:
                self.plugins[all_plugin].main(api_obj)

    def process_plugins(self):
        for p in self.plugins:
            for v in self.plugins[p].arguments['type']:
                try:
                    self.loop[v].append(p)
                except KeyError:
                    self.loop[v] = list()
                    self.loop[v].append(p)
