import requests
import util
import re
import tgapi


class TelegramAPI:
    def __init__(self, config):
        self.misc = dict()
        self.misc['base_url'] = 'https://api.telegram.org/'.format(config.token)
        self.misc['token'] = 'bot{}/'.format(config.token)
        self.misc['session'] = requests.session()
        self.update_id = 0
        self.me = tgapi.get_me(self.misc)
        self.msg = None
        self.plugins = dict()
        self.loop = dict()
        for k in config.plugins:
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)
        self.process_plugins()

    def get_update(self):  # Gets new messages and sends them to plugin_handler
        url = "{}{}getUpdates?offset={}".format(self.misc['base_url'], self.misc['token'], self.update_id)
        response = util.fetch(self.misc['session'], url)
        try:
            parsed_response = response.json()
        except AttributeError:
            print('There seems to be a problem with your connection :(')
            util.timeout('Telegram')
            return None
        for i in parsed_response['result']:
            self.msg = i['message']
            self.route_return(self.route_plugins())
            self.update_id = i['update_id'] + 1  # Updates update_id's value

    def route_return(self, returned_value):  # Figures out where plugin return values belong
        content = {}
        if isinstance(returned_value, str):  # If string sendMessage
            content['text'] = returned_value
            tgapi.send_message(self.misc, self.msg, content)
        elif isinstance(returned_value, dict):
            tgapi.send_method(self.misc, self.msg, returned_value)

    def route_plugins(self):  # Checks if a plugin wants this message then sends to relevant class
        for k in self.loop:
            if k in self.msg:
                run = getattr(self, 'process_{}'.format(k))
                return run()

    def process_plugins(self):
        for p in self.plugins:
            for v in self.plugins[p].arguments['type']:
                try:
                    self.loop[v].append(p)
                except KeyError:
                    self.loop[v] = list()
                    self.loop[v].append(p)

    def process_text(self):
        self.msg['text'] = util.clean_message(self.msg['text'], self.me)
        for x in self.loop['text']:
            for regex in self.plugins[x].arguments['global_regex']:
                match = re.findall(regex, self.msg['text'])
                if match:
                    if type(match[0]) is str:
                        self.msg['match'] = list()
                        self.msg['match'].append(match[0])
                    else:
                        self.msg['match'] = match[0]
                    return self.plugins[x].main(self.msg)

    def process_document(self):

        for x in self.loop['document']:
            self.msg['local_file_path'] = tgapi.download_file(self.misc, self.msg)
            if self.msg['local_file_path'] is not 400:
                return self.plugins[x].main(self.msg)
