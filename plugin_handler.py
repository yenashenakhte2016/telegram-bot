import re


class PluginInit:

    def __init__(self, plugin_list, bot_info):  # Import all plugins from config. Error checking soon(tm)
        self.plugins = {}
        self.msg = None
        self.me = bot_info
        for k in plugin_list:
            plugin = __import__('plugins', fromlist=[k])
            self.plugins[k] = getattr(plugin, k)

    def process_regex(self, msg):  # Loops through plugins checking their regex for a match
        if 'text' in msg:
            self.process_message(msg)
            for x in self.plugins:
                for regex in self.plugins[x].regex:
                    match = re.findall(regex, msg['text'])
                    if match:
                        for index, v in enumerate(match[0]):
                            self.msg['matches{}'.format(index)] = v
                            response = self.plugins[x].main(self.msg)
                            return response

    def process_message(self, msg):  # Removes @bot_username from commands
        self.msg = msg
        username = "@" + self.me['result']['username']
        text = self.msg['text']
        name_match = re.search("^[!#@/]([^ ]*)({})".format(username), text)
        if name_match:
            self.msg['text'] = text.replace(text[:name_match.end(0)], text[:name_match.end(0) - len(username)])
