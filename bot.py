import requests
import util
import re
import tgapi
import threading
import time


class TelegramAPI:
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
        for i in parsed_response['result']:
            run = threading.Thread(target=self.route_plugins, args=(i['message'],))
            run.start()
            if i['update_id'] >= self.update_id:
                self.update_id = i['update_id'] + 1  # Updates update_id's value
        time.sleep(self.config.sleep)

    def route_plugins(self, msg):  # Checks if a plugin wants this message type then sends to relevant class
        if self.time - int(msg['date']) >= 180000:
            for k in self.loop:
                if k in msg:
                    getattr(self, 'process_{}'.format(k))(msg)

    def route_return(self, msg, returned_value):  # Figures out where plugin return values belong
        content = {}
        if isinstance(returned_value, str):  # If string sendMessage
            content['text'] = returned_value
            tgapi.send_message(self.misc, msg, content)
        elif isinstance(returned_value, dict):
            tgapi.send_method(self.misc, msg, returned_value)

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
                    self.route_return(msg, self.plugins[x].main(msg))

    def process_document(self, msg):
        for x in self.loop['document']:
            msg['local_file_path'] = tgapi.download_file(self.misc, msg)
            if msg['local_file_path'] is not 400:
                self.route_return(msg, self.plugins[x].main(msg))
