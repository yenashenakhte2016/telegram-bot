import json


def post_post(session, content):
    response = session.post(**content)
    return response


def fetch(session, url): # Grabs from url and parses as json. note2self, don't make it parse json by default
    response = session.get(url)
    return json.loads(response.text)