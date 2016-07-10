# -*- coding: utf-8 -*-
"""
API Objects for inline queries and callback queries from an inline message
"""

import json
import uuid

import MySQLdb
import _mysql_exceptions
import urllib3.exceptions


class TelegramInlineAPI(object):
    """
    API Object for inline_queries
    https://core.telegram.org/bots/api#inlinequery
    """

    def __init__(self, database, get_me, plugin_name, config, http,
                 inline_query):
        self.database = database
        self.cursor = self.database.cursor()
        self.get_me = get_me
        self.plugin_name = plugin_name
        self.config = config
        self.inline_query = inline_query
        self.http = http
        self.token = self.config['BOT_CONFIG']['token']
        self.message = self.callback_query = None
        self.input_location_message_content = input_location_message_content
        self.input_venue_message_content = input_venue_message_content
        self.input_contact_message_content = input_contact_message_content

    def answer_inline_query(self, results, **kwargs):
        """
        Answers an inline query. The only required argument is results. switch_pm_parameter
        is also inserted into the database for the check_pm_parameters in route_updates if passed
        https://core.telegram.org/bots/api#answerinlinequery
        """
        url = "https://api.telegram.org/bot{}/answerInlineQuery"
        if not isinstance(results, list):
            results = [results]
        package = {
            'inline_query_id': self.inline_query['id'],
            'results': json.dumps(results)
        }
        package.update(kwargs)
        if 'switch_pm_parameter' in kwargs:
            database = MySQLdb.connect(**self.config['DATABASE'])
            parameter = kwargs['switch_pm_parameter']
            cursor = database.cursor()
            try:
                cursor.execute("INSERT INTO pm_parameters VALUES(%s, %s);",
                               (self.plugin_name, parameter))
                database.commit()
            except _mysql_exceptions.IntegrityError:
                pass
            database.close()
        post = self.http.request_encode_body('POST',
                                             url.format(self.token),
                                             fields=package).data
        return json.loads(post.decode('UTF-8'))

    def inline_query_result_article(self, title, input_message_content,
                                    **kwargs):
        """
        Returns a properly formatted InlineQueryResultArticle. Unique IDs are automatically generated.
        The title and input_message_content are the only requred arguments.
        https://core.telegram.org/bots/api#inlinequeryresultarticle
        """
        package = {
            'type': 'article',
            'id': str(uuid.uuid4()),
            'title': title,
            'input_message_content': input_message_content
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_photo(self,
                                  photo,
                                  thumb_url=None,
                                  cached=False,
                                  **kwargs):
        """
        Returns a properly formatted InlineQueryResultPhoto. Unique IDs are automatically generated.
        A photo url or file id are the only required arguments. Set cached to True when passing a file_id.
        When passing a photo url its suggested you pass a thumb_url to reduce loading times though not required.
        https://core.telegram.org/bots/api#inlinequeryresultphoto
        """
        package = {'type': "photo", 'id': str(uuid.uuid4())}
        if cached:
            package['photo_file_id'] = photo
        else:
            package['photo_url'] = photo
            package['thumb_url'] = thumb_url or photo
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_gif(self,
                                gif,
                                thumb_url=None,
                                cached=False,
                                **kwargs):
        """
        Returns a properly formatted InlineQueryResultGif. Unique IDs are automatically generated.
        A gif url or file id are the only required arguments. Set cached to True when passing a file_id.
        When passing a gif url its suggested you pass a thumb_url to reduce loading times though not required.
        https://core.telegram.org/bots/api#inlinequeryresultgif
        """
        package = {'type': "gif", 'id': str(uuid.uuid4())}
        if cached:
            package['gif_file_id'] = gif
        else:
            package['gif_url'] = gif
            package['thumb_url'] = thumb_url or gif
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_mpeg4_gif(self,
                                      mpeg4,
                                      thumb_url=None,
                                      cached=False,
                                      **kwargs):
        """
        Returns a properly formatted InlineQueryResultMpeg4Gif. Unique IDs are automatically generated.
        If passing an mpeg4 url a thumb_url is required. Set cached to True if passing a file_id.
        https://core.telegram.org/bots/api#inlinequeryresultmpeg4gif
        """
        package = {'type': "mpeg4_gif", 'id': str(uuid.uuid4())}
        if cached:
            package['mpeg4_file_id'] = mpeg4
        else:
            package['mpeg4_url'] = mpeg4
            package['thumb_url'] = thumb_url
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_sticker(self, sticker_file_id, **kwargs):
        """
        Returns a properly formatted InlineQueryResultCachedSticker. Unique IDs are automatically generated.
        The only required argument is a file_id.
        https://core.telegram.org/bots/api#inlinequeryresultcachedsticker
        """
        package = {
            'type': "sticker",
            'id': str(uuid.uuid4()),
            'sticker_file_id': sticker_file_id
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_video(self,
                                  title,
                                  video,
                                  mime_type=None,
                                  thumb_url=None,
                                  cached=False,
                                  **kwargs):
        """
        Returns a properly formatted InlineQueryResultVideo. Unique IDs are automatically generated.
        A title alongside a url or file_id are required. When passing a url a thumb_url and mime_type are
        required as well.
        https://core.telegram.org/bots/api#inlinequeryresultaudio
        """
        package = {'type': "video", 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['video_file_id'] = video
        else:
            package['video_url'] = video,
            package['mime_type'] = mime_type,
            package['thumb_url'] = thumb_url
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_audio(self, title, audio, cached=False, **kwargs):
        """
        Returns a properly formatted InlineQueryResultAudio. Unique IDs are automatically generated.
        A title and a file_id or url are the only requirements. When passing a file_id set cached to True.
        https://core.telegram.org/bots/api#inlinequeryresultaudio
        """
        package = {'type': "audio", 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['audio_file_id'] = audio
        else:
            package['audio_url'] = audio
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_voice(self, title, voice, cached=False, **kwargs):
        """
        Returns a properly formatted InlineQueryResultVoice. Unique IDs are automatically generated.
        A title and file_id or url are the only requirements. When passing a file_id set cached to True.
        https://core.telegram.org/bots/api#inlinequeryresultvoice
        """
        package = {'type': 'voice', 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['voice_file_id'] = voice
        else:
            package['voice_url'] = voice,
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_result_document(self,
                               title,
                               document,
                               mime_type=None,
                               cached=False,
                               **kwargs):
        """
        Returns a properly formatted InlineQueryResultDocument. Unique IDs are automatically generated.
        A title and file_id or url are the only requirements. When passing a file_id set cached to True.
        When passing a URL a mime_type is required. Note: Only .zip and .pdf are allowed.
        https://core.telegram.org/bots/api#inlinequeryresultdocument
        """
        package = {'type': "document", 'id': str(uuid.uuid4()), 'title': title}
        if cached:
            package['document_file_id'] = document
        else:
            package['document_url'] = document
            document['mime_type'] = mime_type
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_location(self, title, latitude, longitude,
                                     **kwargs):
        """
        Returns a properly formatted InlineQueryResultLocation. Unique IDs are automatically generated.
        A title, latitude, and longitude are required.
        https://core.telegram.org/bots/api#inlinequeryresultlocation
        """
        package = {
            'type': 'location',
            'id': str(uuid.uuid4()),
            'latitude': latitude,
            'longitude': longitude,
            'title': title
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_result_venue(self, title, latitude, longitude, address,
                            **kwargs):
        """
        Returns a properly formatted InlineQueryResultVenue. Unique IDs are automatically generated.
        A title, latitude, longitude, and address are required.
        https://core.telegram.org/bots/api#inlinequeryresultvenue
        """
        package = {
            'type': 'venue',
            'id': str(uuid.uuid4()),
            'latitude': latitude,
            'longitude': longitude,
            'title': title,
            'address': address
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_query_result_contact(self, phone_number, first_name, **kwargs):
        """
        Returns a properly formatted InlineQueryResultContact. Unique IDs are automatically generated.
        A phone_number and first_name are the only requirements.
        https://core.telegram.org/bots/api#inlinequeryresultcontact
        """
        package = {
            'type': "contact",
            'id': str(uuid.uuid4()),
            'phone_number': phone_number,
            'first_name': first_name
        }
        package.update(kwargs)
        self.add_inline_query(package['id'])
        return package

    def inline_keyboard_markup(self,
                               list_of_list_of_buttons,
                               plugin_data=None):
        """
        Returns an InlineKeyboardMarkup object. Callback data is automatically stored in the
        callback_queries table. Requires a list of lists of buttons.
        https://core.telegram.org/bots/api#inlinekeyboardmarkup
        """
        cursor = self.database.cursor()
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
        cursor.close()
        return package

    def input_text_message_content(self,
                                   message_text,
                                   parse_mode=0,
                                   disable_web_page_preview=False):
        """
        Returns a properly formatted InputTextMessageContent. This is what is sent as the
        result of an inline query. Requires message text. Uses the parse mode specified in
        the config file. disable_web_page_preview is set to false by default.
        https://core.telegram.org/bots/api#inputtextmessagecontent
        """
        if parse_mode == 0:
            parse_mode = self.config['MESSAGE_OPTIONS']['PARSE_MODE']
        return {'message_text': message_text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_web_page_preview}

    def add_inline_query(self, query_id):
        """
        Stores query IDs and corresponding plugin in the inline_queries table. chosen_inline_result
        are then automatically routed back.
        """
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        cursor.execute("INSERT INTO inline_queries VALUES(%s, %s)",
                       (self.plugin_name, query_id))
        cursor.close()
        database.commit()
        database.close()

    def pm_parameter(self, parameter):
        """
        Stores a pm parameter in the pm_parameters table. Requires the parameter and returns
        a formatted URL.
        """
        database = MySQLdb.connect(**self.config['DATABASE'])
        cursor = database.cursor()
        try:
            cursor.execute("INSERT INTO pm_parameters VALUES(%s, %s);",
                           (self.plugin_name, parameter))
        except _mysql_exceptions.IntegrityError:
            pass
        url = "https://telegram.me/{}?start={}"
        bot_name = self.get_me['result']['username']
        cursor.close()
        database.commit()
        database.close()
        return url.format(bot_name, parameter)


def input_location_message_content(latitude, longitude):
    """
    Returns a properly formatted InputLocationMessageContent. Requires a latitude and longitude
    https://core.telegram.org/bots/api#inputlocationmessagecontent
    """
    return {'latitude': latitude, 'longitude': longitude}


def input_venue_message_content(title,
                                latitude,
                                longitude,
                                address,
                                foursquare_id=None):
    """
    Returns a properly formatted InputVenueMessageContent. Requires a title, latitude, longitude
    and address. A foursquare id is optional.
    https://core.telegram.org/bots/api#inputvenuemessagecontent
    """
    package = {
        'latitude': latitude,
        'longitude': longitude,
        'title': title,
        'address': address
    }
    if foursquare_id:
        package['foursquare_id'] = foursquare_id
    return package


def input_contact_message_content(phone_number, first_name, last_name=None):
    """
    Returns a properly formatted InputContactMessageContent. Requires a phone number and first name.
    A last name is optional.
    https://core.telegram.org/bots/api#inputcontactmessagecontent
    """
    package = {'phone_number': phone_number, 'first_name': first_name}
    if last_name:
        package['last_name'] = last_name
    return package


class InlineCallbackQuery(object):
    """
    Represents an Inline Callback query API object.
    """

    def __init__(self, database, config, http, callback_query):
        self.config = config
        self.token = self.config['BOT_CONFIG']['token']
        self.http = http
        self.callback_query = callback_query
        self.database = database
        self.message = self.inline_query = None

    def method(self, method, **kwargs):
        """
        Sends an http request to telegram. Returns the json loaded response if a success and None otherwise
        """
        url = "https://api.telegram.org/bot{}/{}".format(self.token, method)
        try:
            post = self.http.request_encode_body('POST', url, fields=kwargs)
        except urllib3.exceptions.HTTPError:
            return
        if post.status == 200:
            return json.loads(post.data.decode('UTF-8'))

    def answer_callback_query(self,
                              text=None,
                              callback_query_id=None,
                              show_alert=False):
        """
        answerCallbackQuery. Optional arguments are text, callback_query_id and show_alert.
        https://core.telegram.org/bots/api#answercallbackquery
        """
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
        return self.method('answerCallbackQuery', **arguments)

    def edit_message_text(self, text, **kwargs):
        """
        editMessageText. Requires text.
        https://core.telegram.org/bots/api#editmessagetext
        """
        package = {
            'inline_message_id': int(self.callback_query['id']),
            'text': text,
            'parse_mode': self.config['MESSAGE_OPTIONS']['PARSE_MODE']
        }
        package.update(kwargs)
        return self.method('editMessageText', **package)

    def edit_message_caption(self, caption=None, **kwargs):
        """
        editMessageCaption. Use with no arguments to remove a caption.
        https://core.telegram.org/bots/api#editmessagecaption
        """
        package = {'inline_message_id': int(self.callback_query['id'])}
        if caption:
            package['caption'] = caption
        package.update(kwargs)
        return self.method('editMessageCaption', **package)

    def edit_message_reply_markup(self, reply_markup=None, **kwargs):
        """
        editMessageReplyMarkup. Use with no arguments to remove all reply_markup.
        https://core.telegram.org/bots/api#editmessagereplymarkup
        """
        package = {'inline_message_id': int(self.callback_query['id'])}
        if reply_markup:
            package['reply_markup'] = reply_markup
        package.update(kwargs)
        return self.method('editMessageReplyMarkup', **package)
