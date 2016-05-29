import json
import os

import util

base_url = "http://ws.audioscrobbler.com/2.0/?method={}&api_key={}&format=json"
api_key = "f8c3ad637c24265f68a66e3b4c997cc2"
try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


def main(tg):
    tg.send_chat_action('typing')
    if tg.message['flagged_message']:
        link_profile(tg)
    else:
        if tg.message['matched_regex'] == "^/lastfm (.*)":
            first_name = tg.message['match']
            lastfm_name = tg.message['match']
        elif 'reply_to_message' in tg.message:
            first_name = tg.message['reply_to_message']['from']['first_name']
            user_id = tg.message['reply_to_message']['from']['id']
            determiner = "this"
            lastfm_name = get_lastfm_username(user_id)
        else:
            first_name = tg.message['from']['first_name']
            user_id = tg.message['from']['id']
            determiner = "your"
            lastfm_name = get_lastfm_username(user_id)
        if lastfm_name:
            response = last_played(first_name, lastfm_name)
            if response:
                message = response['text']
                keyboard = tg.inline_keyboard_markup(response['keyboard'])
                tg.send_message(message, reply_markup=keyboard)
            else:
                tg.send_message("No recently played tracks :(")
        else:
            tg.send_message("It seems {} LastFM hasn't been linked\n"
                            "Reply with your LastFM to link!".format(determiner), flag_message=True)


def last_played(first_name, lastfm_name):
    track_list = get_recently_played(lastfm_name, 1)
    if track_list:
        for track in track_list:
            profile = "http://www.lastfm.com/user/{}".format(lastfm_name)
            if track['now_playing']:
                message = "{} is currently listening to:\n".format(first_name)
            else:
                message = "{} has last listened to:\n".format(first_name)
            message += "{}\t-\t{}".format(track['song'], track['artist'])
            keyboard = [[{'text': "Profile", 'url': profile}, {'text': "Song", 'url': profile}]]
            return {'text': message, 'keyboard': keyboard}


def get_recently_played(user_name, limit):
    method = 'user.getRecentTracks'
    url = (base_url + '&user={}&limit={}').format(method, api_key, user_name, limit)
    response = util.fetch(url).json()
    if 'error' in response:
        return
    tracks = response['recenttracks']['track']
    track_list = list()
    for track in tracks:
        if '@attr' in track:
            now_playing = True
        else:
            now_playing = False
        song = {
            'song': track['name'],
            'artist': track['artist']['#text'],
            'url': track['url'],
            'album': track['album']['#text'],
            'now_playing': now_playing

        }
        track_list.append(song)
    return track_list


def get_lastfm_username(user_id):
    try:
        with open('data/me/{}.json'.format(user_id)) as json_file:
            profile = json.load(json_file)
    except FileNotFoundError:
        return
    if 'lastfm' in profile:
        return profile['lastfm']


def link_profile(tg):
    if not os.path.exists('data/me'):
        os.makedirs('data/me')
    user_id = tg.message['from']['id']
    try:
        with open('data/me/{}.json'.format(user_id)) as file:
            profile = json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        open('data/me/{}.json'.format(user_id), 'w')
        profile = dict()
    if tg.message['text']:
        if 'lastfm' in profile:
            message = "Updated your LastFM!"
        else:
            message = "Successfully set your LastFM!"
        profile['lastfm'] = tg.message['text'].replace('\n', '')
        response = last_played("You", profile['lastfm'])
        keyboard = None
        if response:
            message += '\n\n' + response['text'].replace(" has", "").replace("is", "are")
            keyboard = tg.inline_keyboard_markup(response['keyboard'])
        tg.send_message(message, reply_markup=keyboard)
    else:
        tg.send_message("Invalid username")
    with open('data/me/{}.json'.format(user_id), 'w') as file:
        json.dump(profile, file, sort_keys=True, indent=4)


plugin_parameters = {
    'name': "LastFM",
    'desc': "View your recently played LastFM tracks!",
    'extended_desc': "The LastFM plugin allows you to share your most recently played song. If your LastFM is linked"
                     "with /me it will automatically utilize your profile. You can also supply an username alongside"
                     "the command, /lastfm.",
    'permissions': True
}

arguments = {
    'text': [
        "^/lastfm$",
        "^/lastfm (.*)"
    ]
}

