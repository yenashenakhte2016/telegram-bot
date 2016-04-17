import requests
import util
import re
import tgapi
import time
from multiprocessing.dummy import Pool


class Bot:
    def __init__(self, config):
        self.config = config
        self.misc = {
            'base_url': 'https://api.telegram.org/',
            'token': 'bot{}/'.format(self.config.token),
            'session': requests.session()
        }
        self.me = tgapi.get_me(self.misc)
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
            parsed_response = response.json()
        except AttributeError:
            print('There seems to be a problem with your connection :(')
            util.timeout('Telegram')
            return None
        pool = Pool()
        pool.map(self.route_plugins, parsed_response['result'])
        pool.close()
        pool.join()
        time.sleep(self.config.sleep)

    def route_plugins(self, msg):  # Checks if a plugin wants this message type then sends to relevant class
        if msg['update_id'] >= self.update_id:
            self.update_id = msg['update_id'] + 1  # Updates update_id's value
        msg = msg['message']
        if self.time - int(msg['date']) <= 180000:
            for k in self.loop:
                if k in msg:
                    getattr(self, 'process_{}'.format(k))(msg)

    def process_plugins(self):
        for p in self.plugins:
            for v in self.plugins[p].arguments['type']:
                try:
                    self.loop[v].append(p)
                except KeyError:
                    self.loop[v] = list()
                    self.loop[v].append(p)

    def process_text(self, msg):
        msg['text'] = util.clean_message(msg['text'], self.me)
        for x in self.loop['text']:
            for regex in self.plugins[x].arguments['global_regex']:
                match = re.findall(regex, msg['text'])
                if match:
                    if type(match[0]) is str:
                        msg['match'] = list()
                        msg['match'].append(match[0])
                    else:
                        msg['match'] = match[0]
                    api_obj = tgapi.PluginHelper(msg, self.misc)
                    self.plugins[x].main(api_obj)

    def process_document(self, msg):
        for x in self.loop['document']:
            msg['local_file_path'] = tgapi.download_file(self.misc, msg)
            if msg['local_file_path'] is not 400:
                api_obj = tgapi.PluginHelper(msg, self.misc)
                self.plugins[x].main(api_obj)
