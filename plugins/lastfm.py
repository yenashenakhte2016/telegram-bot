import json
import os

base_url = "http://ws.audioscrobbler.com/2.0/?method={}&api_key={}&format=json"
api_key = "f8c3ad637c24265f68a66e3b4c997cc2"
try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError


def main(tg):
    if tg.message:
        handle_message(tg)


def handle_message(tg):
    tg.send_chat_action('typing')
    if tg.message['flagged_message']:
        link_profile(tg)
    else:
        first_name, lastfm_name, determiner = determine_names(tg)
        if lastfm_name:
            response = last_played(tg.http, first_name, lastfm_name)
            if response:
                message = response['text']
                tg.send_message(message, reply_markup=tg.inline_keyboard_markup(response['keyboard']))
            else:
                tg.send_message("No recently played tracks :(")
        else:
            tg.send_message("It seems {} LastFM hasn't been linked\n"
                            "Reply with your LastFM to link it!".format(determiner), flag_message=True)


def determine_names(tg):
    if tg.message['matched_regex'] == "^/lastfm (.*)":
        determiner = None
        lastfm_name = first_name = tg.message['match']
    elif 'reply_to_message' in tg.message:
        user_id = tg.message['reply_to_message']['from']['id']
        determiner = "this"
        lastfm_name = get_lastfm_username(user_id)
        first_name = tg.message['reply_to_message']['from']['first_name']
    else:
        user_id = tg.message['from']['id']
        determiner = "your"
        lastfm_name = get_lastfm_username(user_id)
        first_name = tg.message['from']['first_name']
    return first_name, lastfm_name, determiner


def last_played(http, first_name, lastfm_name):
    track_list = get_recently_played(http, lastfm_name, 1)
    if track_list:
        for track in track_list:
            if track['now_playing']:
                message = "{} is currently listening to:\n".format(first_name)
            else:
                message = "{} has last listened to:\n".format(first_name)
            message += "{}\t-\t{}".format(track['song'], track['artist'])
            keyboard = create_keyboard(lastfm_name, track['url'])
            return {'text': message, 'keyboard': keyboard}
    elif track_list is None:
        print('invalid message')


def create_keyboard(lastfm_name, song_url):
    profile_url = "http://www.lastfm.com/user/{}".format(lastfm_name)
    return [[{'text': "Profile", 'url': profile_url}, {'text': "Song", 'url': song_url}]]


def get_recently_played(local_http, user_name, limit):
    method = 'user.getRecentTracks'
    url = (base_url + '&user={}&limit={}').format(method, api_key, user_name, limit)
    result = local_http.request('GET', url).data
    response = json.loads(result.decode('UTF-8'))
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
        with open('data/profile/{}.json'.format(user_id)) as json_file:
            profile = json.load(json_file)
    except FileNotFoundError:
        return
    if 'lastfm' in profile:
        return profile['lastfm']


def link_profile(tg):
    if not os.path.exists('data/profile'):
        os.makedirs('data/profile')
    user_id = tg.message['from']['id']
    try:
        with open('data/profile/{}.json'.format(user_id)) as file:
            profile = json.load(file)
    except (JSONDecodeError, FileNotFoundError):
        open('data/profile/{}.json'.format(user_id), 'w')
        profile = dict()
    if tg.message['text']:
        if 'lastfm' in profile:
            message = "Updated your LastFM!"
        else:
            message = "Successfully set your LastFM!"
        profile['lastfm'] = tg.message['text'].replace('\n', '')
        track_list = get_recently_played(tg.http, profile['lastfm'], 1)
        keyboard = None
        if track_list:
            track_list = track_list.pop()
            if track_list['now_playing']:
                message += "\n\nYou are currently listening to:"
            else:
                message += "\n\nYou have last listened to:"
            message += "\n{} - {}".format(track_list['song'], track_list['artist'])
            keyboard = create_keyboard(profile['lastfm'], track_list['url'])
        tg.send_message(message, reply_markup=tg.inline_keyboard_markup(keyboard))
    else:
        tg.send_message("Invalid username")
    with open('data/profile/{}.json'.format(user_id), 'w') as file:
        json.dump(profile, file, sort_keys=True, indent=4)


plugin_parameters = {
    'name': "LastFM",
    'desc': "View your recently played LastFM tracks!",
    'extended_desc': "The LastFM plugin allows you to share your most recently played song. If your LastFM is linked"
                     "with /profile it will automatically utilize your profile. You can also supply an username "
                     "alongside the command, /lastfm.",
    'permissions': True
}

arguments = {
    'text': [
        "^/lastfm$",
        "^/lastfm (.*)"
    ]
}
