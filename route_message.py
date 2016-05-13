import re

import tgapi
import util
import logging


class RouteMessage:
    def __init__(self, message, package, check_db_only=False):
        self.log = logging.getLogger(__name__)
        self.package = package
        self.message = message
        self.message['flagged_message'] = None
        self.message['matched_regex'] = None
        self.message['matched_argument'] = None
        self.log.debug('Received message {}'.format(self.message['message_id']))
        if self.check_db() and not check_db_only:
            self.plugin_check()

    def check_db(self):
        if 'text' in self.message:
            self.message['text'] = util.clean_message(self.message['text'], self.package[1]['username'])
        reply_to_message = 'reply_to_message' in self.message
        private_chat = self.message['chat']['type'] == 'private'
        if reply_to_message or private_chat:
            message_id = self.message['reply_to_message']['message_id'] if reply_to_message else None
            chat_id = self.message['chat']['id']
            self.log.debug('Checking message with id {} from chat {} in db'.format(message_id, chat_id))
            db_selection = self.package[4].select(['plugin_id', 'user_id'],
                                                  'flagged_messages',
                                                  conditions=[('message_id', message_id),
                                                              ('chat_id', chat_id)],
                                                  return_value=True, single_return=True)
            if db_selection:
                self.log.info('Flagged message {} triggered in chat {}'.format(message_id, chat_id))
                self.message['flagged_message'] = True
                self.package[4].delete('flagged_messages', [('message_id', message_id), ('chat_id', chat_id)])
                self.package[3][db_selection[0]].main(tgapi.TelegramApi(self.message, self.package, db_selection[0]))
                return False
        return True

    def plugin_check(self):
        for plugin in self.package[3]:
            for key, value in plugin.arguments.items():
                if self.check_argument(key, value, self.message):
                    self.log.info('Plugin {} triggered'.format(plugin.__name__))
                    plugin.main(tgapi.TelegramApi(self.message, self.package, self.package[3].index(plugin)))

    def check_argument(self, key, value, incremented_message):
        self.log.debug('Checking {} with value {}'.format(key, value))
        if key in incremented_message:
            if type(value) is list:
                incremented_message = incremented_message[key]
                return self.check_match(key, value, incremented_message)
            elif type(value) is dict:
                incremented_message = incremented_message[key]
                for key1, value1 in value.items():
                    if self.check_argument(key1, value1, incremented_message):
                        return True
        else:
            return False

    def check_match(self, key, values, incremented_message):
        self.log.debug('Received key {} and values {}'.format(key, values))
        self.message['matched_argument'] = key
        if '*' in values:
            self.log.debug('Found * in values, returning')
            self.message['matched_regex'] = '*'
            return True
        for regex in values:
            match = re.findall(str(regex), str(incremented_message))
            if match:
                self.log.debug('Matched {} to message'.format(regex))
                self.message['matched_regex'] = regex
                self.message['match'] = match[0]
                return True
        self.log.debug('No match')
        return False
