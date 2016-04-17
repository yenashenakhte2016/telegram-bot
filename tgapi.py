import util
from functools import partial


class TelegramApi:
    def __init__(self, message, misc):
        self.msg = message
        self.misc = misc
        self.send_photo = partial(self.send_something, 'sendPhoto')
        self.send_audio = partial(self.send_something, 'sendAudio')
        self.send_document = partial(self.send_something, 'sendDocument')
        self.send_sticker = partial(self.send_something, 'sendSticker')
        self.send_video = partial(self.send_something, 'sendVideo')
        self.send_voice = partial(self.send_something, 'sendVoice')
        self.get_user_profile_photos = partial(self.simple_send_something, 'getUserProfilePhotos')
        self.kick_chat_member = partial(self.simple_send_something, 'kickChatMember', chat_id=self.msg['chat']['id'])
        self.unban_chat_member = partial(self.simple_send_something, 'unbanChatMember', chat_id=self.msg['chat']['id'])

    def send_chat_action(self, action, chat_id=0):
        if type(chat_id) != int or chat_id is 0:
            chat_id = self.msg['chat']['id']
        package = dict()
        package['data'] = {
            'chat_id': chat_id,
            'action': action
        }
        send_method(self.misc, package, 'sendChatAction')

    def send_something(self, method, file, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'reply_to_message_id': self.msg['message_id']
        }
        package['files'] = file
        for k, v in kwargs.items():
            package['data'][k] = v
        send_method(self.misc, package, method)

    def simple_send_something(self, method, user_id, **kwargs):
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
        send_method(self.misc, package, 'sendMessage')

    def send_location(self, latitude, longitude, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'latitude': latitude,
            'longitude': longitude
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        send_method(self.misc, package, 'sendLocation')

    def send_venue(self, latitude, longitude, title, address, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'latitude': latitude,
            'longitude': longitude,
            'title': title,
            'address': address
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        send_method(self.misc, package, 'sendVenue')

    def send_contact(self, phone_number, first_name, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'phone_number': phone_number,
            'first_name': first_name
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        send_method(self.misc, package, 'sendContact')

    def get_user_profile_photos(self, user_id, **kwargs):
        package = dict()
        package['data'] = {
            'user_id': user_id
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        return send_method(self.misc, package, 'sendContact')

    def get_file(self, file_id, download=False):
        package = dict()
        package['data'] = {
            'file_id': file_id
        }
        response = send_method(self.misc, package, 'getFile').json()
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

    def forward_message(self, message_id, from_chat_id, **kwargs):
        package = dict()
        package['data'] = {
            'chat_id': self.msg['chat']['id'],
            'message_id': message_id,
            'from_chat_id': from_chat_id
        }
        for k, v in kwargs.items():
            package['data'][k] = v
        return send_method(self.misc, package, 'forwardMessage')

    def get_me(self):
        return get_me(self.misc)


def send_method(misc, returned_value, method, base_url='{0}{1}{2}'):  # If dict is returned
    package = {'url': base_url.format(misc['base_url'], misc['token'], method)}
    for k, v in returned_value.items():
        package[k] = v
    response = util.post_post(package, misc['session']).json()
    return response['result']


def get_me(misc):  # getMe
    url = "{}{}getMe".format(misc['base_url'], misc['token'])
    response = util.fetch(url, misc['session'])
    parsed_response = response.json()
    return parsed_response['result']
