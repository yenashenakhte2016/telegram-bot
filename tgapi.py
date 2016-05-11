from functools import partial
import logging
import util


class TelegramApi:
    def __init__(self, message, package, plugin_id):
        self.msg = message
        self.package = package
        self.plugin_id = plugin_id
        self.log = logging.getLogger(__name__)
        self.send_photo = partial(self.send_file, 'sendPhoto')
        self.send_audio = partial(self.send_file, 'sendAudio')
        self.send_document = partial(self.send_file, 'sendDocument')
        self.send_sticker = partial(self.send_file, 'sendSticker')
        self.send_video = partial(self.send_file, 'sendVideo')
        self.send_voice = partial(self.send_file, 'sendVoice')
        self.get_user_profile_photos = partial(self.send_text, 'getUserProfilePhotos')
        self.kick_chat_member = partial(self.send_text, 'kickChatMember', chat_id=self.msg['chat']['id'])
        self.unban_chat_member = partial(self.send_text, 'unbanChatMember', chat_id=self.msg['chat']['id'])
        self.edit_message_text = partial(self.send_text, 'editMessageText')
        self.edit_message_caption = partial(self.send_text, 'editMessageCaption')
        self.edit_message_reply_markup = partial(self.send_text, 'editMessageReplyMarkup')
        self.send_location = partial(self.send_text, 'sendLocation')
        self.send_venue = partial(self.send_text, 'sendVenue')
        self.send_contact = partial(self.send_text, 'sendContact')
        self.forward_message = partial(self.send_text, 'forwardMessage')
        self.answer_callback_query = partial(self.send_text, 'answerCallbackQuery')
        self.get_user_profile_photos = partial(self.send_text,
                                               'getUserProfilePhotos',
                                               chat_id=self.msg['chat']['id'])

    def send_chat_action(self, action, chat_id=False):
        if not chat_id:
            chat_id = self.msg['chat']['id']
        package = dict()
        package['data'] = {
            'chat_id': chat_id,
            'action': action
        }
        self.log.info('sendChatAction "{}" to {}'.format(action, chat_id))
        return self.send_method(package, 'sendChatAction')

    def send_file(self, method, file=None, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id']
        }
        if self.msg['chat']['type'] != 'private':
            package['data'].update({'reply_to_message_id': self.msg['message_id']})
        if file:
            package['files'] = file
        for k, v in kwargs.items():
            package['data'][k] = v
        self.log.info('{} to {}'.format(method, package['data']['chat_id']))
        return self.send_method(package, method)

    def send_text(self, method, user_id, **kwargs):
        package = dict()
        package['data'] = {
            'user_id': user_id
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        self.log.info('{} to {}'.format(method, package['data']['chat_id']))
        return self.send_method(package, package, method)

    def send_message(self, text, flag_message=False, flag_user_id=None, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'text': text,
            'parse_mode': "HTML"
        }
        if self.msg['chat']['type'] != 'private':
            package['data'].update({'reply_to_message_id': self.msg['message_id']})
        for k, v in kwargs.items():
            package['data'][k] = v
        self.log.info('sendMessage to {} and flag_message={}'.format(package['data']['chat_id'], flag_message))
        if flag_message:
            message = self.send_method(package, 'sendMessage')
            self.flag_message(message_id=message['message_id'], chat_id=message['chat']['id'], user_id=flag_user_id)
            return message
        else:
            return self.send_method(package, 'sendMessage')

    def send_method(self, data, method, base_url='{0}{1}{2}'):  # General function for sending methods
        data['url'] = base_url.format(self.package[0][0], self.package[0][1], method)
        response = util.post(data, self.package[2]).json()
        if not response['ok']:
            self.log.error('Error received in response: {}'.format(response))
            return response
        else:
            return response['result']

    def get_file(self, file_id, download=False):
        package = dict()
        package['data'] = {
            'file_id': file_id
        }
        response = self.send_method(package, 'getFile')
        self.log.info('Grabbing file {} and download={}'.format(file_id, download))
        if download:
            return self.download_file(response)
        else:
            return response

    def download_file(self, file_object):
        url = "{}/file/{}{}".format(self.package[0][0], self.package[0][1], file_object['file_path'])
        try:
            name = file_object['file_path']
        except KeyError:
            name = None
        file_name = util.name_file(file_object['file_id'], name)
        file_path = util.fetch_file(url, 'data/files/{}'.format(file_name), self.package[2])
        self.log.info('Downloaded file {} in /data/files/'.format(file_name, file_path))
        return file_path

    def flag_message(self, plugin=None, message_id=None, chat_id=None, user_id=None):  # Flags a message in the DB
        if not plugin:
            plugin_id = self.plugin_id
        else:
            v = self.package[4].select('plugin_id', 'plugins',
                                       conditions=[('plugin_name', plugin)],
                                       return_value=True,
                                       single_return=True)
            plugin_id = v[0]
        if user_id is True:
            user_id = self.msg['from']['id']
        if self.msg['chat']['type'] == 'private':
            self.package[4].delete('flagged_messages', [('chat_id', chat_id)])
        if message_id and chat_id:
            self.package[4].insert('flagged_messages', [plugin_id, message_id, chat_id, user_id])
