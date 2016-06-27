import json
import concurrent.futures

base_url = "https://danbooru.donmai.us"
api_key = None


def main(tg):
    global api_key
    api_key = tg.config['DANBOORU']['api_key']
    page = int(tg.inline_query['offset']) if tg.inline_query['offset'] else 1
    query = "rating:s" if tg.inline_query['matched_regex'] == inline_arguments[0] else tg.inline_query['match'][1]
    result = get_post(tg.http, query, page)
    if result:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        futures = [executor.submit(create_box, tg, pic) for pic in result]
        concurrent.futures.wait(futures)
        offset = page + 1 if len(result) == 40 else ''
        response = [box.result() for box in futures]
        tg.answer_inline_query([box for box in response if box], cache_time=86400, next_offset=offset)
    else:
        tg.answer_inline_query([], cache_time=86400)


def create_box(tg, pic):
    try:
        image_url = base_url + pic['file_url']
    except KeyError:
        return
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
    'name': "Danbooru",
    'short_description': "Search for anime art inline using animepic <search_term>",
    'long_description': "This is an inline only function which allows you to search Danbooru for anime art. Simply "
                        "initiate an inline query from any chat and type in <code>animepic &lt;search_term&gt;</code>.",
    'inline_only': True
}

inline_arguments = [
    '^/?(danbooru|animepic)$',
    '^/?(danbooru|animepic) (.*)'
]
