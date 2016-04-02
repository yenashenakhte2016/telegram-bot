import re
import bettermain


class PluginInit:

    def __init__(self, plugin_list):
        self.plugins = {}
        for k in plugin_list:
            self.plugins[k] = __import__(k)

    def process_regex(self, msg):
        msg['text'] = process_message(msg['text'])
        for x in self.plugins:
            for regex in self.plugins:
                match = re.search(regex, msg['text'])
                if match:
                    return x


def process_message(text):  # Removes @bot_username from commands
    username = bettermain.getMe['result']['username']
    name_match = re.search("^[!#@/]([^ ]*)(@{})".format(username), text)
    if name_match:
        return text.replace(text[:name_match.end(0) - len(username) + 1], text[:name_match.end(0)])
    return text
