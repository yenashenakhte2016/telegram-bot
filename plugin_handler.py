import re


class PluginInit:

    def __init__(self, config, bot_info):  # Import all plugins from config. Error checking soon(tm)
        self.plugins = {}
        self.msg = None
        self.loop = {}
        self.me = bot_info
        for k in config.plugins:
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)
        self.process_plugins()

    def process_regex(self, msg):  # Loops through plugins checking their regex for a match
        if 'text' in msg:
            self.process_message(msg)
            for x in self.loop['text']:
                for regex in self.plugins[x].arguments['global_regex']:
                    match = re.findall(regex, msg['text'])
                    if match:
                        if type(match[0]) is str:
                            self.msg['match'] = list()
                            self.msg['match'].append(match[0])
                        else:
                            self.msg['match'] = match[0]
                        return self.plugins[x].main(self.msg)

    def process_message(self, msg):  # Removes @bot_username from commands
        self.msg = msg
        username = "@" + self.me['result']['username']
        text = self.msg['text']
        name_match = re.search('^[!#@/]([^ ]*)({})'.format(username), text)
        if name_match:
            self.msg['text'] = text.replace(text[:name_match.end(0)], text[:name_match.end(0) - len(username)])

    def process_plugins(self):
        for p in self.plugins:
            self.loop['text'] = []
            if 'text' in self.plugins[p].arguments['type']:
                self.loop['text'].append(p)
