import sys
from functools import partial

import util


class TelegramApi:
    def __init__(self, message, misc, db, plugin):
        self.msg = message
        self.misc = misc
        self.db = db
        self.plugin = plugin
        self.send_photo = partial(self.send_file, 'sendPhoto')
        self.send_audio = partial(self.send_file, 'sendAudio')
        self.send_document = partial(self.send_file, 'sendDocument')
        self.send_sticker = partial(self.send_file, 'sendSticker')
        self.send_video = partial(self.send_file, 'sendVideo')
        self.send_voice = partial(self.send_file, 'sendVoice')
        self.get_user_profile_photos = partial(self.send_text, 'getUserProfilePhotos')
        self.kick_chat_member = partial(self.send_text, 'kickChatMember', chat_id=self.msg['chat']['id'])
        self.unban_chat_member = partial(self.send_text, 'unbanChatMember', chat_id=self.msg['chat']['id'])
        self.get_user_profile_photos = partial(self.send_text,
                                               'getUserProfilePhotos',
                                               chat_id=self.msg['chat']['id'])
        self.edit_message_text = partial(self.send_text, 'editMessageText')
        self.edit_message_caption = partial(self.send_text, 'editMessageCaption')
        self.edit_message_reply_markup = partial(self.send_text, 'editMessageReplyMarkup')
        self.send_location = partial(self.send_text, 'sendLocation')
        self.send_venue = partial(self.send_text, 'sendVenue')
        self.send_contact = partial(self.send_text, 'sendContact')
        self.forward_message = partial(self.send_text, 'forwardMessage')
        self.answer_callback_query = partial(self.send_text, 'answerCallbackQuery')

    def get_me(self):
        return get_me(self.misc)

    def send_chat_action(self, action, chat_id=0):
        if type(chat_id) != int or chat_id is 0:
            chat_id = self.msg['chat']['id']
        package = dict()
        package['data'] = {
            'chat_id': chat_id,
            'action': action
        }
        return send_method(self.misc, package, 'sendChatAction')

    def send_file(self, method, file=None, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'reply_to_message_id': self.msg['message_id']
        }
        if file:
            package['files'] = file
        for k, v in kwargs.items():
            package['data'][k] = v
        return send_method(self.misc, package, method)

    def send_text(self, method, user_id, **kwargs):
        package = dict()
        package['data'] = {
            'user_id': user_id
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        return send_method(self.misc, package, method)

    def send_message(self, text, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'text': text,
            'parse_mode': "HTML",
            'reply_to_message_id': self.msg['message_id']
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        return send_method(self.misc, package, 'sendMessage')

    def get_file(self, file_id, download=False):
        package = dict()
        package['data'] = {
            'file_id': file_id
        }
        response = send_method(self.misc, package, 'getFile')
        if download:
            return self.download_file(response)
        else:
            return response

    def download_file(self, file_object):
        url = "{}/file/{}{}".format(self.misc['base_url'], self.misc['token'], file_object['file_path'])
        try:
            name = file_object['file_path']
        except KeyError:
            name = None
        file_name = util.name_file(file_object['file_id'], name)
        file_path = util.fetch_file(url, 'data/files/{}'.format(file_name), self.misc['session'])
        return file_path

    def temp_argument(self, plugin=None, message_id=None, chat_id=None):
        plugin_id = None
        if not plugin:
            plugin = self.plugin
        self.db.execute('SELECT plugin_id FROM plugins WHERE plugin_name="{}"'.format(plugin))
        for v in self.db.db:
            plugin_id = v[0]
        if message_id and chat_id:
            self.db.execute('INSERT INTO temp_arguments VALUES({},{},{})'.format
                            (plugin_id, message_id, chat_id))


def send_method(misc, returned_value, method, base_url='{0}{1}{2}'):  # If dict is returned
    package = {'url': base_url.format(misc['base_url'], misc['token'], method)}
    for k, v in returned_value.items():
        package[k] = v
    response = util.post(package, misc['session']).json()
    if response['ok']:
        return response['result']
    else:
        print("There seems to be an error in the response :(")
        print(response)
        sys.exit()


def get_me(misc):  # getMe
    url = "{}{}getMe".format(misc['base_url'], misc['token'])
    response = util.fetch(url, misc['session']).json()
    if response['ok']:
        return response['result']
    else:
        print("There seems to be an error :(\nCheck your API key and connection to the internet")
        print(response)
        sys.exit()
