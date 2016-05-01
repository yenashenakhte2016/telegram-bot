import requests
import util
import re
from tgapi import TelegramApi
from tgapi import get_me
import time
import concurrent.futures
import db


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
        self.bot_db = None

    def init(self):
        self.bot_db = db.Database('bot')
        self.bot_db.execute("""drop table if exists plugins""")
        self.bot_db.execute("""create table plugins (
        plugin_id int primary key not NULL,
        plugin_name text,
        pretty_name text,
        description text,
        usage text)""")
        for i, k in enumerate(self.config.plugins):
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)
            try:
                pretty_name = self.plugins[k].plugin_info['name']
            except KeyError:
                print('Plugin {} is missing a name.\nPlease add it to "plugin_info"')
                self.plugins[k].plugin_info['name'] = k
                pretty_name = self.plugins[k].plugin_info['name']
            try:
                desc = self.plugins[k].plugin_info['desc']
            except KeyError:
                print('Plugin {} is missing a description.\nPlease add it to "plugin_info"')
                desc = None
            try:
                usage = self.plugins[k].plugin_info['usage']
            except KeyError:
                usage = None
            self.bot_db.execute('insert into plugins values({},"{}","{}","{}","{}")'.format
                                (i, k, pretty_name, desc, usage))

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
            with concurrent.futures.ThreadPoolExecutor() as e:
                for i in response['result']:
                    if self.time - int(i['message']['date']) <= 180:
                        e.submit(self.route_message, TelegramApi(i['message'], self.misc))
            time.sleep(self.config.sleep)
        else:
            print('Error fetching new messages:\nCode: {}'.format(response['error_code']))
            time.sleep(self.config.sleep)

    def route_message(self, api_obj):  # Routes where plugins go
        loop = True

        if 'text' in api_obj.msg:
            api_obj.msg['text'] = util.clean_message(api_obj.msg['text'], self.me['username'])
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
                                    return check_match(regex, built_msg)
                    if type(values) is list:
                        for regex in values:
                            return check_match(regex, built_msg)
                    return

                def check_match(regex, built_msg):
                    if regex is '*':
                        self.plugins[plugin].main(api_obj)
                        return True
                    else:
                        match = re.findall(str(regex), str(built_msg))
                        if match:
                            if type(match[0]) is str:
                                api_obj.msg['match'] = list()
                                api_obj.msg['match'].append(match[0])
                            else:
                                api_obj.msg['match'] = match[0]
                            self.plugins[plugin].main(api_obj)
                            return True

                for args, nested_arg in self.plugins[plugin].plugin_info['arguments'].items():
                    x = argument_loop(args, nested_arg, api_obj.msg)
                    if x:
                        loop = False
                        break
