import config
import log
import json
import requests
import re
import sys

plugins = {}
update_id = 0
run = True
baseurl = "https://api.telegram.org/bot%s" % config.API
text_file = open("output.txt", "a", encoding="utf-8")
session = requests.Session()

print("\033[1m####BOT####\033[1;m")
update = session.get(baseurl + "/getMe")
botinfo = json.loads(update.text)
if botinfo['ok']:
    print("{0}[\033[1;32m@{1}\033[1;m]".format(botinfo['result']['first_name'], botinfo['result']['username']))
    print("ID: {0}".format(botinfo['result']['id']))
else:
    print("\033[1;31m[✖]\033[1;m There seems to be something wrong with your api key in config.py :(")
    sys.exit(0)
print("\033[1m####ADMINS####\033[1;m")
for admin in config.admins:
    print("\033[1;32m[✓]\033[1;m " + str(admin))
print("\033[1m####PLUGINS####\033[1;m")
for plugin in config.plugins:
    sys.path.append("./plugins")
    plugins[plugin] = __import__(plugin)
    if plugins[plugin].main and plugins[plugin].regex and plugins[plugin].pluginname:
        print("\033[1;32m[✓]\033[1;m " + plugins[plugin].pluginname)
    else:
        print("\033[1;31m[✖]\033[1;m " + plugin)
        del plugins[plugin]


def shutdown():
    global run
    run = False
    text_file.close()
    print("Shutting down for now :(")


def sendmessage(sendmessageObject):
    response = session.post(
        url=baseurl + "/sendMessage",
        data=sendmessageObject
    ).json()
    return response


def sendmessagedefault(chatid, text, replyid):
    response = session.post(
        url=baseurl + "/sendMessage",
        data={'chat_id': chatid, 'text': text, 'reply_to_message_id': replyid, 'parse_mode': "Markdown"}
    ).json()
    return response


def checktrigger(msg):
    for x in plugins:
        for regex in plugins[x].regex:
            msg['rawtext'] = msg['text']
            msg['text'] = msg['text'].replace("@{0}".format(botinfo['result']['username']), "")
            match = re.search(regex, msg['text'])
            if match is not None:
                rval = plugins[x].main(msg)
                if isinstance(rval, str):
                    sendmessagedefault(msg['chat']['id'], rval, msg['message_id'])
                elif isinstance(rval, dict):
                    sendmessage(rval)
                return


while run:
    update = session.get(baseurl + "/getUpdates?offset=%s" % update_id)
    getupdate = json.loads(update.text)
    for i in range(len(getupdate['result'])):
        msg = getupdate['result'][i]['message']
        log.main(msg, text_file)
        if 'text' in msg:
            checktrigger(msg)
        if i == len(getupdate['result']) - 1:
            update_id = getupdate['result'][i]['update_id'] + 1
