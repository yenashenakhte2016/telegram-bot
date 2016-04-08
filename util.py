import json


def make_request(session, url, content):
    response = session.post(
        url=url,
        data=content
    ).json()
    return response


def fetch(session, url):
    response = session.get(url)
    return json.loads(response.text)
