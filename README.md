# Hitagibot

Hitagibot is a plugin based Telegram bot written in python 3 and
licensed under the GNU Affero General Public License V3.
The bot focuses on providing a lightweight and high performance modular environment for bot creation.

###Setup
- ```bash git clone https://github.com/TopBakuhatsu/nanobotpython.git```
- Then add your api key to config.ini

After this you can run the bot!
- ```bash cd hitagibot```
- ```bash python3 main.py```

###Plugins
Plugins are simple to make. Every plugin will need: 

**`plugin_info`**

Here is where you should place plugin information. This includes a pretty name, short description, and list of commands.

**`arguments`**

Arguments can be specified which when met will trigger the plugin. As of now there are two types, ```text``` and
```document```. See ```echo.py``` for an example. Plugins which look for text can specify a ```global_regex```
and for files ```mime_type```.

regex should be a list containing all "triggers" for your plugin. Use [regex101](https://regex101.com/) to create and test them.

**`main`** 

main will always be the function where you receive the ```TelegramApi``` object. Through here you can interact with the
telegram api. The message object can be easily accessed with ```TelegramApi.msg```, this is the equivalent of
[this](https://core.telegram.org/bots/api#message). Here is an example plugin:

```python
def main(tg_api):
    tg_api.send_chat_action('typing')
    if 'Hello' in tg_api.msg['text']:
        tg_api.send_message('Hey!')
    elif 'Bye' in tg_api.msg['text']:
        tg_api.send_message('Bye :(')
```

###What can it do?
| Method               | Status |
| -------------------- | ------ |
| getMe                | ✔      |
| sendMessage          | ✔      |
| forwardMessage       | ✔      |
| sendPhoto            | ✔      |
| sendAudio            | ✔      |
| sendDocument         | ✔      |
| sendSticker          | ✔      |
| sendVideo            | ✔      |
| sendVoice            | ✔      |
| sendLocation         | ✔      |
| SendVenue            | ✔      |
| SendContact          | ✔      |
| sendChatActions      | ✔      |
| getUserProfilePhotos | ✔      |
| getFile              | ✔      |
| kickChatMember       | ✔      |
| unbanChatMember      | ✔      |
| answerCallbackQuery  | ✖      |
| Updating Messages    | ✖      |
| Inline Mode          | ✖      |


Notes:
- All supported telegram methods are lower_case_with_underscores
- Optional arguments can be sent with methods.
For example ```tg_api.send_message('*Hey!*', parse_mode='Markdown')``` will work. Even
required arguments can be overwritten, for example ```chat_id```.
- getFile can be given the argument ```download=True``` and the local path to the file
will be returned. You can also manually do this using ```tg_api.download_file(document_object)```
which is what getFile will return otherwise.
- For plugins which utilize requests its a good idea to piggy back off the ```util.py``` module.
It will have various useful functions for fetching data.
- This read.me is probably outdated

