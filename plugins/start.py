def main(tg_api):
    tg_api.send_chat_action('typing')
    first_name = tg_api.package[1]['first_name']
    message = "Hi, I'm {}! A multipurpose telegram bot written in python 3. You can see a list of my commands using " \
              "/help. You can also view my source code <a href='https://github.com/TopBakuhatsu/hitagibot'>here</a>" \
        .format(first_name)
    tg_api.send_message(message, disable_web_page_preview=True, reply_to_message_id=None)


plugin_info = {
    'name': "Start",
    'desc': "Introduces the bot!",
    'usage': ['/start']
}

arguments = {
    'text': [
        "^[/]start$"
    ]
}
