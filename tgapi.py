import collections
import logging
from functools import partial

import util


class TelegramApi:
    def __init__(self, message, package, plugin_id):
        self.message = message
        self.package = package
        self.plugin_id = plugin_id
        self.log = logging.getLogger(__name__)
        self.send_photo = partial(self.send_file, 'sendPhoto')
        self.send_audio = partial(self.send_file, 'sendAudio')
        self.send_document = partial(self.send_file, 'sendDocument')
        self.send_sticker = partial(self.send_file, 'sendFile')
        self.send_video = partial(self.send_file, 'sendVideo')
        self.send_voice = partial(self.send_file, 'sendVoice')
        self.edit_message_reply_markup = partial(self.edit_content, 'editMessageReplyMarkup')

    def method(self, method_name, check_content=True, **kwargs):
        content = dict()
        content['data'] = dict()
        content['url'] = '{0}{1}{2}'.format(self.package[0][0], self.package[0][1], method_name)
        if check_content:
            if self.message['chat']['type'] != 'private':
                content['data'].update({'reply_to_message_id': self.message['message_id']})
            if 'chat_id' not in kwargs:
                content['data'].update({'chat_id': self.message['chat']['id']})
            if 'file' in kwargs:
                content['files'] = kwargs.pop('file')
        content['data'].update(kwargs)
        response = util.post(content, self.package[2]).json()
        if not response['ok']:
            self.log.error('Error with response\nResponse: {}'.format(response))
        return response

    def send_message(self, text, flag_message=False, **kwargs):
        arguments = {'text': text, 'parse_mode': 'HTML'}
        arguments.update(kwargs)
        response = self.method('sendMessage', **arguments)
        if flag_message and response['ok']:  # Will crash if response attribute error
            msg = response['result']
            self.flag_message(flag_message)
        return response

    def forward_message(self, message_id, **kwargs):
        if 'chat_id' not in kwargs:
            kwargs['chat_id'] = kwargs['chat_id'] or self.message['chat']['id']
        return self.method('sendMessage', **locals())

    def send_file(self, method, file, **kwargs):
        arguments = locals()
        del arguments['self']
        del arguments['method']
        return self.method(method, **arguments)

    def send_location(self, latitude, longitude, **kwargs):
        arguments = locals()
        del arguments['self']
        arguments.update(arguments.pop('kwargs'))
        return self.method('sendLocation', **arguments)

    def send_venue(self, latitude, longitude, title, address, **kwargs):
        arguments = locals()
        del arguments['self']
        arguments.update(arguments.pop('kwargs'))
        return self.method('sendVenue', **arguments)

    def send_contact(self, phone_number, first_name):
        arguments = locals()
        del arguments['self']
        arguments.update(arguments.pop('kwargs'))
        return self.method('sendContact', **arguments)

    def send_chat_action(self, action, **kwargs):
        arguments = locals()
        del arguments['self']
        arguments.update(arguments.pop('kwargs'))
        return self.method('sendChatAction', **arguments)

    def get_user_profile_photos(self, user_id, offset=0, limit=0):
        return self.method('getUserProfilePhotos', check_content=False, **locals())

    def get_file(self, file_id):
        return self.method('getFile', check_content=False, file_id=file_id)

    def kick_chat_member(self, user_id, chat_id=None):
        arguments = locals()
        del arguments['self']
        if not arguments['chat_id']:
            del arguments['chat_id']
        return self.method('kickChatMember', **arguments)

    def unban_chat_member(self, user_id, chat_id=None):
        arguments = locals()
        del arguments['self']
        if not arguments['chat_id']:
            del arguments['chat_id']
        return self.method('unbanChatMember', **arguments)

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        return self.method('answerCallbackQuery', check_content=False, **locals())

    def edit_content(self, method, **kwargs):
        arguments = kwargs
        if 'chat_id' and 'inline_message_id' not in arguments:
            if 'message_id' in arguments:
                arguments.update({'chat_id': self.message['chat']['id']})
            else:
                return 'ERROR: Need chat_id + message_id or inline_message_id'
        return self.method(method, check_content=False, **arguments)

    def edit_message_text(self, text, **kwargs):
        arguments = locals()
        del arguments['self']
        arguments.update(arguments.pop('kwargs'))
        return self.edit_content('editMessageText', **arguments)

    def edit_message_caption(self, **kwargs):
        if 'caption' and 'reply_markup' not in kwargs:
            return 'ERROR: Need caption or reply_markup'
        return self.edit_content('editMessageText', **kwargs)

    def flag_message(self, parameters):
        default = [('plugin_id', self.plugin_id),
                   ('message_id', self.message['message_id']),
                   ('chat_id', self.message['chat']['id']),
                   ('user_id', self.message['from']['id']),
                   ('single_use', False),
                   ('currently_active', True)]
        merged_parameters = collections.OrderedDict(default)
        if type(parameters) is dict():
            merged_parameters.update(parameters)
        self.package[4].insert('flagged_messages', list(merged_parameters.values()))

    def download_file(self, file_object):
        conditions = [('file_id', file_object['file_id'])]
        selection = self.package[4].select('file_path', 'downloads', conditions=conditions, single_return=True)
        if selection:
            return selection[0]
        else:
            url = "{}/file/{}{}".format(self.package[0][0], self.package[0][1], file_object['file_path'])
            try:
                name = file_object['file_path']
            except KeyError:
                name = None
            file_name = util.name_file(file_object['file_id'], name)
            return util.fetch_file(url, 'data/files/{}'.format(file_name), self.package[2])
