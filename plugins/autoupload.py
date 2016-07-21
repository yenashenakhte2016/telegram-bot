"""
Uploads a compressed version of uncompressed images.
"""

import io
from PIL import Image


def main(tg):
    """
    Ignores gifs. Downloads an image, downscales, then uploads as a jpeg.
    """
    if 'gif' in tg.message['document']['mime_type']:
        return
    document_obj = tg.get_file(tg.message['document']['file_id'])
    tg.send_chat_action('upload_photo')
    file_path = tg.download_file(document_obj)
    photo = Image.open(file_path)
    photo = resize_image(photo)
    photo = compress_image(photo)
    name = document_obj['result']['file_id'] + ".jpg"
    tg.send_photo((name, photo.read()),
                  disable_notification=True,
                  reply_to_message_id=tg.message['message_id'])


def resize_image(image):
    """
    Resizes an image if its height or width > 1600. Uses lanczos downscaling.
    """
    if image.size[0] > 1600 or image.size[1] > 1600:
        larger = image.size[0] if image.size[0] > image.size[
            1] else image.size[1]
        scale = 1600 / larger
        new_dimensions = (int(image.size[0] * scale),
                          int(image.size[1] * scale))
        return image.resize(new_dimensions, Image.LANCZOS)
    return image


def compress_image(image):
    """
    Saves a jpeg copy of the image in a BytesIO object with quality set to 100.
    """
    compressed_image = io.BytesIO()
    image.save(compressed_image, format='JPEG', quality=100)
    image.close()
    compressed_image.seek(0)
    return compressed_image


parameters = {
    'name': "Auto upload",
    'short_description':
    "Automatically uploads your uncompressed images for you",
    'permissions': "11"
}

arguments = {'document': {'mime_type': ['image']}}
