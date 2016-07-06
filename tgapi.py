# -*- coding: utf-8 -*-

import _io
import hashlib
import json
import os
import re
import time
from functools import partial

import MySQLdb
import _mysql_exceptions


class TelegramApi:
    def __init__(self,
                 database,
                 get_me,
                 plugin_name,
                 config,
                 http,
                 message=None,
                 plugin_data=None,
                 callback_query=None):
        self.database = database
        self.database.autocommit(True)
        self.cursor = self.database.cursor()
        self.get_me = get_me
        self.inline_query = None
        self.http = http
        self.plugin_name = plugin_name
        self.config = config
        self.token = self.config['BOT_CONFIG']['token']

        self.message = message
        self.plugin_data = plugin_data
        self.callback_query = callback_query

        self.send_photo = partial(self.send_file, 'sendPhoto')
        self.send_audio = partial(self.send_file, 'sendAudio')
        self.send_document = partial(self.send_file, 'sendDocument')
        self.send_sticker = partial(self.send_file, 'sendFile')
        self.send_video = partial(self.send_file, 'sendVideo')
        self.send_voice = partial(self.send_file, 'sendVoice')
        self.get_chat = partial(self.get_something, 'getChat')
        self.get_chat_administrators = partial(self.get_something,
                                               'getChatAdministrators')
        self.get_chat_members_count = partial(self.get_something,
                                              'getChatMembersCount')

        self.reply_keyboard_hide = reply_keyboard_hide
        self.reply_keyboard_markup = reply_keyboard_markup
        self.force_reply = force_reply

        self.last_sent = None
        if self.message:
            self.chat_data = self.message
        elif self.callback_query:
            self.chat_data = self.callback_query['message']

    def method(self, method_name, check_content=True, **kwargs):
        content = dict()
        content['data'] = dict()
        url = "https://api.telegram.org/bot{}/{}".format(self.token,
                                                         method_name)

        if check_content:
            if self.chat_data['chat']['type'] != 'private' and eval(
                    self.config['MESSAGE_OPTIONS']['reply_in_groups']):
                kwargs['reply_to_message_id'] = self.chat_data['message_id']
            elif eval(self.config['MESSAGE_OPTIONS']['reply_in_private']):
                print(self.config['MESSAGE_OPTIONS']['reply_in_private'])
                kwargs['reply_to_message_id'] = self.chat_data['message_id']
            if 'chat_id' not in kwargs:
                kwargs['chat_id'] = self.chat_data['chat']['id']

        post = self.http.request_encode_body('POST', url, fields=kwargs).data
        return json.loads(post.decode('UTF-8'))

    def get_something(self, method, chat_id=None):
        chat_id = chat_id or self.chat_data['chat']['id']
        return self.method(method, check_content=False, chat_id=chat_id)

    def send_message(self, text, flag_message=None, **kwargs):
        arguments = {'text': text,
                     'parse_mode':
                     self.config['MESSAGE_OPTIONS']['PARSE_MODE']}
        arguments.update(kwargs)
        response = self.method('sendMessage', **arguments)
        if response['ok']:
            self.last_sent = {
                'message_id': response['result']['message_id'],
                'chat_id': response['result']['chat']['id']
            }
            if flag_message:
                message_id = response['result']['message_id']
                if type(flag_message) is not dict:
                    flag_message = dict()
                self.flag_message(message_id, flag_message)
        return response

    def forward_message(self,
                        chat_id,
                        message_id=None,
                        from_chat_id=None,
                        disable_notification=False):
        if not message_id:
            message_id = self.message['message_id']
        if not from_chat_id:
            from_chat_id = self.message['chat']['id']
        package = {
            'chat_id': chat_id,
            'message_id': message_id,
            'from_chat_id': from_chat_id,
            'disable_notification': disable_notification
        }
        return self.method('forwardMessage', **package)

    def send_file(self, method, file, **kwargs):
        database = MySQLdb.connect(**self.config['DATABASE'])
        arguments = kwargs
        file_type = method.replace('send', '').lower()
        if type(file) is str:
            arguments.update({file_type: file})
            return self.method(method, **arguments)
        elif type(file) != tuple:
            file_name = os.path.basename(file.name)
            if type(file) is _io.BufferedReader:
                file = file.read()
            file = (file_name, file)
        try:
            md5 = hashlib.md5(file[1]).hexdigest()
            database.query(
                'SELECT file_id FROM uploaded_files WHERE file_hash="{}" '
                'AND file_type = "{}"'.format(md5, file_type))
            query = database.store_result()
            row = query.fetch_row(how=1)
            if row:
                arguments.update({file_type: row[0]['file_id']})
                return self.method(method, **arguments)
        except TypeError:
            md5 = None
        arguments.update({file_type: file})
        result = self.method(method, **arguments)
        if result['ok']:
            try:
                file_id = result['result'][file_type]['file_id']
            except TypeError:
                file_id = result['result'][file_type][-1]['file_id']
            if md5:
                cursor = database.cursor()
                cursor.execute("INSERT INTO uploaded_files VALUES(%s, %s, %s)",
                               (file_id, md5, file_type))
        database.commit()
        database.close()
        return result

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
        arguments = locals()
        del arguments['self']
        return self.method('getUserProfilePhotos',
                           check_content=False,
                           **arguments)

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

    def answer_callback_query(self,
                              text=None,
                              callback_query_id=None,
                              show_alert=False):
        arguments = locals()
        del arguments['self']
        if not callback_query_id:
            try:
                arguments.update(
                    {'callback_query_id': int(self.callback_query['id'])})
            except KeyError:
                return "Callback query ID not found!"
        if text is None:
            del arguments['text']
        return self.method('answerCallbackQuery',
                           check_content=False,
                           **arguments)

    def edit_message_text(self, text, **kwargs):
        message_id, chat_id = self.get_edit_parameters()
        package = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': self.config['MESSAGE_OPTIONS']['PARSE_MODE']
        }
        package.update(kwargs)
        return self.method('editMessageText', check_content=False, **package)

    def edit_message_caption(self, caption=None, **kwargs):
        message_id, chat_id = self.get_edit_parameters()
        package = {'chat_id': chat_id, 'message_id': message_id}
        if caption:
            package['caption'] = caption
        package.update(kwargs)
        return self.method('editMessageCaption',
                           check_content=False,
                           **package)

    def edit_message_reply_markup(self, reply_markup=None, **kwargs):
        message_id, chat_id = self.get_edit_parameters()
        package = {'chat_id': chat_id, 'message_id': message_id}
        if reply_markup:
            package['reply_markup'] = reply_markup
        package.update(kwargs)
        return self.method('editMessageReplyMarkup',
                           check_content=False,
                           **package)

    def get_edit_parameters(self):
        if self.last_sent:
            message_id = self.last_sent['message_id']
            chat_id = self.last_sent['chat_id']
        elif self.message and 'reply_to_message' in self.message:
            message_id = self.message['reply_to_message']['message_id']
            chat_id = self.message['chat']['id']
        elif self.callback_query:
            message_id = self.callback_query['message']['message_id']
            chat_id = self.callback_query['message']['chat']['id']
        else:
            message_id = None
            chat_id = None
        return message_id, chat_id

    def flag_message(self, message_id, parameters):
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        plugin_name = parameters[
            'plugin_name'] if 'plugin_name' in parameters else self.plugin_name
        message_id = message_id
        chat_id = parameters[
            'chat_id'] if 'chat_id' in parameters else self.chat_data['chat'][
                'id']
        user_id = parameters['user_id'] if 'user_id' in parameters else None
        currently_active = parameters[
            'currently_active'] if 'currently_active' in parameters else True
        single_use = parameters[
            'single_use'] if 'single_use' in parameters else 0
        plugin_data = json.dumps(parameters[
            'plugin_data']) if 'plugin_data' in parameters else None
        cursor.execute(
            "UPDATE flagged_messages SET currently_active=0 WHERE chat_id=%s",
            (chat_id, ))
        cursor.execute(
            "INSERT INTO flagged_messages VALUES(%s, %s, %s, %s, %s, %s, %s)",
            (plugin_name, message_id, chat_id, user_id, currently_active,
             single_use, plugin_data))
        database.commit()
        database.close()

    def flag_time(self, reminder_time, plugin_data=None, plugin_name=None):
        if self.message:
            reminder_id = "{}-{}-{}".format(self.message['message_id'],
                                            self.message['chat']['id'],
                                            time.time())
        else:
            reminder_id = "{}-{}-{}".format(self.callback_query['id'],
                                            self.callback_query['from']['id'],
                                            time.time())
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        plugin_name = plugin_name or self.plugin_name
        plugin_data = json.dumps(plugin_data) if plugin_data else None
        self.chat_data.update({'reminder_id': reminder_id})
        previous_message = json.dumps(self.chat_data)
        cursor.execute(
            "INSERT INTO flagged_time VALUES(%s, %s, FROM_UNIXTIME(%s), %s, %s)",
            (reminder_id, plugin_name, reminder_time, previous_message,
             plugin_data))
        database.commit()
        database.close()
        return reminder_id

    def download_file(self, file_object):
        database = MySQLdb.connect(**self.config['DATABASE'])
        file_id = file_object['result']["file_id"]
        file_path = file_object['result']['file_path']
        database.query(
            'SELECT file_path FROM downloaded_files WHERE file_id="{}";'.format(
                file_id))
        query = database.store_result()
        row = query.fetch_row(how=1)
        if row:
            database.close()
            return row[0]['file_path']
        else:
            cursor = database.cursor()
            url = "https://api.telegram.org/file/bot{}/{}".format(self.token,
                                                                  file_path)
            try:
                name = file_path
            except KeyError:
                name = None
            file_name = name_file(file_id, name)
            path = 'data/files/{}'.format(file_name)
            request = self.http.request('get', url)
            with open(path, 'wb') as output:
                file_hash = hashlib.md5(request.data).hexdigest()
                output.write(request.data)
            cursor.execute("INSERT INTO downloaded_files VALUES(%s, %s, %s)",
                           (file_id, path, file_hash))
            database.commit()
            database.close()
            return path

    def inline_keyboard_markup(self,
                               list_of_list_of_buttons,
                               plugin_data=None):
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        plugin_data = json.dumps(plugin_data)
        for button_list in list_of_list_of_buttons:
            for button in button_list:
                if 'text' not in button:
                    return "Error: Text not found in button object"
                if 'callback_data' in button:
                    try:
                        cursor.execute(
                            "INSERT INTO callback_queries VALUES(%s, %s, %s)",
                            (self.plugin_name, button['callback_data'],
                             plugin_data))
                    except _mysql_exceptions.IntegrityError:
                        continue
        package = {'inline_keyboard': list_of_list_of_buttons}
        database.commit()
        database.close()
        return json.dumps(package)

    def get_chat_member(self, user_id, chat_id=None, check_db=True):
        if check_db:
            database = MySQLdb.connect(**self.config['DATABASE'])
            database.query(
                "SELECT first_name, last_name, user_name FROM users_list WHERE user_id={}".format(
                    user_id))
            query = database.store_result()
            result = query.fetch_row(how=1)
            if result:
                user_obj = {'id': user_id}
                user_obj.update(result[0])
                return {'result': {'status': 'from_db',
                                   'user': user_obj},
                        'ok': True}
        chat_id = chat_id or self.chat_data['chat']['id']
        return self.method('getChatMember',
                           check_content=False,
                           user_id=user_id,
                           chat_id=chat_id)


def reply_keyboard_markup(list_of_list_of_buttons,
                          resize_keyboard=False,
                          one_time_keyboard=False,
                          selective=False):
    for button_list in list_of_list_of_buttons:
        for button in button_list:
            if 'text' not in button:
                return "Error: Text not found in button object"
    package = {
        'keyboard': list_of_list_of_buttons,
        'resize_keyboard': resize_keyboard,
        'one_time_keyboard': one_time_keyboard,
        'selective': selective
    }
    return json.dumps(package)


def reply_keyboard_hide(hide_keyboard=True, selective=False):
    package = {'hide_keyboard': hide_keyboard, 'selective': selective}
    return json.dumps(package)


def force_reply(forced_reply=True, selective=False):
    package = {'force_reply': forced_reply, 'selective': selective}
    return json.dumps(package)


def name_file(file_id, file_name):
    if file_name:
        match = re.findall('(\.[0-9a-zA-Z]+$)', file_name)
        if match:
            return file_id + match[0]
    return str(file_id)
