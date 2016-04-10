import json


def make_post(session, url, content):  # Simple post request
    response = session.post(
        url=url,
        data=content
    ).json()
    return response


def fetch(session, url): # Grabs from url and parses as json. note2self, don't make it parse json by default
    response = session.get(url)
    return json.loads(response.text)


def throw(session, url, file, data):  # Combine with into 1
    response = session.post(url=url, files=file, data=data)
    return response
