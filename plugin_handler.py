import re
import sys


class PluginInit:

    def __init__(self, plugin_list, bot_info):  # Import all plugins from config. Error checking soon(tm)
        self.plugins = {}
        self.msg = None
        self.me = bot_info
        for k in plugin_list:
            sys.path.append("./plugins")  # Need to replace this with a better solution
            self.plugins[k] = __import__(k)  # "plugins." + k seems to not work

    def process_regex(self, msg):  # Loops through plugins checking their regex for a match
        if 'text' in msg:
            self.msg = msg
            self.process_message()
            for x in self.plugins:
                for regex in self.plugins[x].regex:
                    match = re.findall(regex, msg['text'])
                    if match:
                        for index, v in enumerate(match[0]):
                            self.msg['matches{}'.format(index)] = v
                            response = self.plugins[x].main(self.msg)
                            return response
        else:
            return None  # For now only text works.

    def process_message(self):  # Removes @bot_username from commands
        username = "@" + self.me['result']['username']
        text = self.msg['text']
        name_match = re.search("^[!#@/]([^ ]*)({})".format(username), text)
        if name_match:
            self.msg['text'] = text.replace(text[:name_match.end(0)], text[:name_match.end(0) - len(username)])
        return
