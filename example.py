pluginname = "" #Put the name of your plugin here

regex = [ #Put triggers here. It uses regex, handy site: https://regex101.com/
"^[!@#\/]ayy$",
"^[!@#\/]ayy2$"
]

'''
Main should always be your main function. You will recieve the object msg and return from here.
msg is the same as the message object in the telegram bot api: https://core.telegram.org/bots/api
'''
def main(msg):
    return "*lmao*"
