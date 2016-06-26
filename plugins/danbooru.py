import json
import concurrent.futures

base_url = "https://danbooru.donmai.us"
api_key = None


def main(tg):
    global api_key
    api_key = tg.config['DANBOORU']['api_key']
    page = int(tg.inline_query['offset']) if tg.inline_query['offset'] else 1
    query = "rating:s" if tg.inline_query['matched_regex'] == inline_arguments[0] else tg.inline_query['match']
    result = get_post(tg.http, query, page)
    if result:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        futures = [executor.submit(create_box, tg, pic) for pic in result]
        concurrent.futures.wait(futures)
        offset = page + 1 if len(result) == 40 else ''
        tg.answer_inline_query([box.result() for box in futures], cache_time=0, next_offset=offset)
    else:
        tg.answer_inline_query([], cache_time=0)


def create_box(tg, pic):
    image_url = base_url + pic['file_url']
    thumb_url = base_url + pic['preview_file_url']
    keyboard = [[{'text': 'Full Resolution', 'url': base_url + pic['large_file_url']}]]
    width = pic['image_width']
    height = pic['image_height']
    return tg.inline_query_result_photo(image_url, thumb_url, photo_width=width, photo_height=height,
                                        reply_markup=tg.inline_keyboard_markup(keyboard))


def get_post(http, tags, page):
    fields = {
        'api_key': api_key,
        'limit': 40,
        'tags': tags.replace(' ', '_') + ' rating:safe',
        'page': page
    }
    request = http.request('GET', base_url + '/posts.json', fields=fields)
    if request.status == 200:
        try:
            return json.loads(request.data.decode('UTF-8'))
        except json.decoder.JSONDecodeError:
            return
    else:
        return request.status


parameters = {
    'name': "Danbooru Search",
    'short_description': "Search Danbooru for anime art inline using: animepic <query>",
    'inline_only': True
}

inline_arguments = [
    '^/?(danbooru|animepic)$',
    '^/?(danbooru|animepic) (.*)'
]
