# Hitagibot

Hitagi is a plugin based Telegram bot written in Python 3 and licensed
under the GNU Affero General Public License v3. 

## Installation
You will need python 3 (3.5.1 is recommended) to use the bot.

First clone and cd to the repository
```bash
git clone https://github.com/TopBakuhatsu/hitagibot.git
cd hitagibot
```
Give the plugin permission to execute
```bash
chmod +x hitagi.py
```
Install required dependencies
```bash
pip install -r requirements.txt
```
Finally set your token in the config.ini. You can get a token from 
@BotFather on the Telegram client.
```
token = YOUR TOKEN HERE
```
#Notes:

* Some plugins may require separate tokens for their services
* OSx users will need to install OpenSSL & Python3 from homebrew in order for the bot to function properly
* This bot does not work on Windows without significant modifications

Now you can start the bot with `./hitagi.py`. Plugin documentation is
available on the wiki for more advanced users.
