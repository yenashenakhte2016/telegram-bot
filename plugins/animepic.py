import json
import time
import concurrent.futures

base_url = "https://ibsearch.xxx/api/v1/images.json"
image_path = "https://{}.ibsearch.xxx/{}"
thumb_path = "https://{}.ibsearch.xxx/t{}"
api_key = None


def main(tg):
    global api_key
    api_key = tg.config['IBSEARCH']['api_key']
    if not api_key:
        return
    if tg.inline_query:
        page = int(tg.inline_query['offset']) if tg.inline_query['offset'] else 1
        if tg.inline_query['matched_regex'] == inline_arguments[0]:
            query = 'random: rating:s'
        else:
            query = tg.inline_query['match'].replace(' ','') + ' rating:s'
        images = get_images(tg.http, query, page=page)
        if images:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
            futures = [executor.submit(create_box, tg.inline_query_result_photo, pic) for pic in images]
            concurrent.futures.wait(futures)
            offset = page + 1 if len(images) == 50 else ''
            tg.answer_inline_query([box.result() for box in futures], cache_time=86400, next_offset=offset)
        else:
            tg.answer_inline_query([], cache_time=0)


def create_box(inline_query_result_photo, pic):
    image_url = image_path.format(pic['server'], pic['path'])
    thumb_url = thumb_path.format(pic['server'], pic['path'])
    width = int(pic['width'])
    height = int(pic['height'])
    return inline_query_result_photo(image_url, thumb_url, photo_width=width, photo_height=height)


def get_images(http, query, limit=50, page=1):
    fields = {
        'key': api_key,
        'limit': limit,
        'page': page,
        'q': query,
        'rating': 's'
    }
    response = http.request('GET', base_url, fields=fields)
    if response.status == 200:
        try:
            return json.loads(response.data.decode('UTF-8'))
        except json.decoder.JSONDecodeError:
            return
    elif response.status == 429:
        time.sleep(0.1)
        get_images(http, query)
    else:
        return response.status


parameters = {
    'name': "AnimePic",
    'short_description': "Search for anime pictures inline by typing in @hitagibot animepic"
}

inline_arguments = [
    'animepic$',
    'animepic (.*)',
    '/animepic (.*)'
]
