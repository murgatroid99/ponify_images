from flask import Flask, request, make_response
import json
import requests
from bs4 import BeautifulSoup
from PIL import Image
import urllib2
import random
import io
import cgi
import re
from config import api_key

BASE_URL = "http://api.tumblr.com/v2/blog/{blog}/posts/?offset={offset}&api_key=" + api_key

app = Flask(__name__)

blogs = ("friendshipismagicgifs.tumblr.com", "mlp-gifs.tumblr.com", "animatedponies.tumblr.com", "pinkie-pie.tumblr.com")

class Photo(object):
    def __init__(self, width, height, url):
        self.width = width
        self.height = height
        self.url = url

from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

def get_images(blog):
    num_posts = 1
    offset = 0
    while num_posts > 0:
        res = requests.get(BASE_URL.format(blog=blog, offset=offset))
        if res.ok:
            posts = json.loads(res.text)["response"]["posts"]
            for post in posts:
                if post["type"] == "photo":
                    for photo in post["photos"]:
                        orig = photo["original_size"]
                        yield Photo(orig["width"], orig["height"], orig["url"])
                elif post["type"] == "text":
                    soup = BeautifulSoup(post["body"])
                    for img in soup("img"):
                        url = img["src"]
                        try:
                            fd = urllib2.urlopen(url)
                            width, height = Image.open(io.BytesIO(fd.read())).size
                            yield Photo(width, height, url)
                        except (urllib2.HTTPError, IOError):
                            continue
                num_posts = len(posts)
                offset += num_posts
            else:
                break

blog_images = {blog: list(get_images(blog)) for blog in blogs}

def get_closeness_measure(width, height):
    ratio = float(width)/float(height)
    def closeness(photo):
        ratio2 = float(photo.width)/float(photo.height)
        return (abs(ratio-ratio2), abs(width - photo.width))

@app.route("/image/<int:width>/<int:height>", methods=["GET"])
@crossdomain(origin="*")
def get_image(width, height):
    if width<1 or height<1:
        return ''
    blog = random.choice(blogs)
    closeness = get_closeness_measure(width, height)
    images = sorted(blog_images[blog], key=closeness)
    image_url = random.choice(images[:20]).url
    return image_url

@app.route("/bookmarklet")
def get_bookmarklet():
    with open("ponify.js") as ponify:
        output = "<h1>Ponify all images on a web page</h1>"
        output += "<p>The following link is a bookmarklet: drag it onto the bookmarks bar and then click it on any site</p>"
        output += "<p><pre><code>{0}</code></pre></p>"
        output += '<p><a href="javascript:{0}">Ponify Images</a></p>'
        script = re.sub(r'\s*\n\s*', '', ponify.read())
        return output.format(script)

if __name__ == "__main__":
    app.debug = True
    print ("ready")
    app.run()
