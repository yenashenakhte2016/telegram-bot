import requests
import util
import re


class TelegramAPI:
    def __init__(self, config):
        self.url = {
            'base': 'https://api.telegram.org/'.format(config.token),
            'token': 'bot{}/'.format(config.token)
        }
        self.session = requests.session()
        self.update_id = 0
        self.me = self.get_me()
        self.msg = None
        self.plugins = dict()
        self.loop = dict()
        for k in config.plugins:
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)
        self.process_plugins()

    def get_update(self):  # Gets new messages and sends them to plugin_handler
        url = "{}{}getUpdates?offset={}".format(self.url['base'], self.url['token'], self.update_id)
        response = util.fetch(self.session, url)
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
            self.send_message(content)
        elif isinstance(returned_value, dict):
            self.send_method(returned_value)

    def get_me(self):  # getMe
        url = "{}{}getMe".format(self.url['base'], self.url['token'])
        response = util.fetch(self.session, url)
        parsed_response = response.json()
        return parsed_response

    def send_message(self, content):  # If String is returned
        package = dict()
        package['url'] = "{}{}sendMessage".format(self.url['base'], self.url['token'])
        package['data'] = {  # Default return
            'chat_id': self.msg['chat']['id'],
            'text': "",
            'parse_mode': "HTML",
            'reply_to_message_id': self.msg['message_id']
        }
        package['data']['text'] = content['text']
        util.post_post(self.session, package)

    def send_method(self, returned_value):  # If dict is returned
        method = returned_value['method']
        del returned_value['method']
        package = {'url': "{}{}{}".format(self.url['base'], self.url['token'], method)}
        for k, v in returned_value.items():
            package[k] = v
        try:
            if 'chat_id' not in package['data']:  # Makes sure a chat_id is provided
                package['data']['chat_id'] = self.msg['chat']['id']
        except KeyError:
            package['data'] = dict()
            package['data']['chat_id'] = self.msg['chat']['id']
        util.post_post(self.session, package)

    def download_file(self, file_id):
        package = dict()
        package['url'] = "{}{}getFile".format(self.url['base'], self.url['token'])
        package['data'] = {'file_id': file_id}
        response = util.post_post(self.session, package).json()
        if response['ok']:
            url = "{}/file/{}{}".format(self.url['base'], self.url['token'], response['result']['file_path'])
            try:
                name = self.msg['document']['file_name']
            except KeyError:
                name = None
            file_name = util.name_file(file_id, name)
            response = util.fetch_file(self.session, url, 'data/files/{}'.format(file_name))
            return response
        else:
            return response['error_code']

    def route_plugins(self):  # Checks if a plugin wants this message then sends to relevant class
        for k in self.loop:
            if k in self.msg:
                run = getattr(self, 'process_{}'.format(k))
                return run()

    def process_message(self):  # Removes @bot_username from commands
        username = "@" + self.me['result']['username']
        text = self.msg['text']
        name_match = re.search('^[!#@/]([^ ]*)({})'.format(username), text)
        if name_match:
            self.msg['text'] = text.replace(text[:name_match.end(0)], text[:name_match.end(0) - len(username)])

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
            self.msg['local_file_path'] = self.download_file(self.msg['document']['file_id'])
            if self.msg['local_file_path'] is not 400:
                return self.plugins[x].main(self.msg)
