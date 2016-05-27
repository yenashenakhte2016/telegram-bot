import json
import util
import os

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
        last_played(tg)


def last_played(tg):
    if tg.message['matched_regex'] == arguments['text'][1]:
        this_or_your = 'this'
        username = tg.message['match']
    else:
        this_or_your = 'your'
        user_id = tg.message['from']['id']
        username = get_lastfm_username(user_id)
        if not username:
            tg.send_message(
                "It seems that your LastFM isn't linked :(\nReply with your username to set!", flag_message=True)
            return
    track_list = get_recently_played(username)
    if track_list == 'error':
        tg.send_message("It seems {} profile is invalid :(".format(this_or_your))
    elif track_list:
        track_list = track_list[0]
        artist = track_list['artist']
        song = track_list['song']
        url = track_list['url']
        user = tg.message['from']['first_name']
        profile = "http://www.lastfm.com/user/{}".format(username)
        keyboard = [[{'text': 'Profile', 'url': profile}, {'text': 'Song', 'url': url}]]
        if track_list['now_playing']:
            tg.send_message("{} is currently listening to:\n{} - {}".format(user, song, artist),
                            reply_markup=tg.inline_keyboard_markup(keyboard))
        else:
            tg.send_message("{} last listened to:\n{} - {}".format(user, song, artist),
                            reply_markup=tg.inline_keyboard_markup(keyboard))
    else:
        tg.send_message("It seems you haven't listened to anything recently :(")


def get_recently_played(user_name, limit=1):
    method = 'user.getRecentTracks'
    url = (base_url + '&user={}&limit={}').format(method, api_key, user_name, limit)
    response = util.fetch(url).json()
    if 'error' in response:
        return 'error'
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
        profile['lastfm'] = tg.message['text'] if len(tg.message['text']) <= 15 else None
        tg.send_message(message)
    else:
        tg.send_message("Invalid username")
    with open('data/me/{}.json'.format(user_id), 'w') as file:
        json.dump(profile, file, sort_keys=True, indent=4)


plugin_info = {
    'name': "LastFM",
    'desc': "View your recently played LastFM tracks!",
    'usage': [
        "/lastfm"
    ],
}

arguments = {
    'text': [
        "^/lastfm$",
        "^/lastfm (.*)"
    ]
}
