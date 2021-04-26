import os
import sys
import math
import random
import getopt
import string
import bcrypt
import aggdraw
from PIL import Image
from PIL import ImageFilter
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from datetime import datetime
from io import BytesIO  # for Python3

import django

os.environ["DJANGO_SETTINGS_MODULE"] = 'generate_captcha.settings'
django.setup()

from captchaimages.models import ImgCaptcha

DIR = '/home/hanh/Desktop/generate/generate_captcha/'
DATA_DIR = os.path.join(DIR, 'data')
IMAGE_DIR = os.path.join(DIR, 'images')
DEFAULT_FONTS = os.path.join(DATA_DIR, 'DroidSansMono.ttf')
FONT_SIZE = 70


class Captcha(object):
    def generate(self, chars, format='png'):
        """generate an images captcha of given characters"""
        """chars: text to be generated
            format: images file format"""
        im = self.generate_image(chars)
        """create BytesIO like file object"""
        out = BytesIO()
        im.save(out, format=format)
        """return back to the start"""
        out.seek(0)
        return out

    def write(self, chars, output, format='png'):
        im = self.generate_image(chars)
        return im.save(output, format=format)


class ImageCaptcha(Captcha):
    """ create an images captcha """

    def __init__(self, width=270, height=100, fonts=None, font_sizes=None):
        self._width = width
        self._height = height
        self._fonts = fonts or DEFAULT_FONTS
        self._font_sizes = font_sizes or FONT_SIZE
        self._truefonts = []

    @property
    def truefonts(self):
        if self._truefonts:
            return self._truefonts
        self._truefonts = tuple([
            truetype(n, FONT_SIZE)
            for n in self._fonts
        ])
        """truetype returns a font object"""
        return self._truefonts

    @staticmethod
    def create_noisy_dots(image, number):
        w, h = image.size
        color = random_color(10, 200, random.randint(220, 225))
        while number:
            x1 = random.randint(0, w)
            y1 = random.randint(0, h)
            points = [x1, y1]
            Draw(image).point(points, fill=color)
            number -= 1
        return image

    @staticmethod
    def create_noisy_circles(image, number):
        w, h = image.size
        while number:
            distance = random.randint(1, 10)
            x1 = random.randint(0, w)
            x2 = x1 + distance
            y1 = random.randint(0, h)
            y2 = y1 + distance

            points = [x1, y1, x2, y2]
            draw = Draw(image)
            color = random_color(10, 200, random.randint(220, 225))
            draw.ellipse(points, fill=color, outline=color)
            number -= 1
        return image

    @staticmethod
    def create_noisy_triangle(image, number):
        w, h = image.size
        while number:
            distance = random.randint(1, 10)
            x1 = random.randint(int(w / 10), w - int(w / 10))
            x2 = x1 + distance
            y1 = random.randint(int(h / 10), h - int(h / 10))
            y2 = y1

            dx = x2 - x1
            dy = y2 - y1

            alpha = 60. / 180 * math.pi
            x3 = x1 + math.cos(alpha) * dx + math.sin(alpha) * dy
            y3 = y1 + math.sin(-alpha) * dx + math.cos(alpha) * dy

            points = [x1, y1, x2, y2, x3, y3]
            color = random_color(10, 200, random.randint(220, 225))
            draw = Draw(image)
            draw.polygon(points, fill=color)
            number -= 1
        return image

    @staticmethod
    def create_noisy_curve(image, number):
        w, h = image.size
        while number:
            x1 = random.randint(0, int(w / 5))
            x2 = random.randint(int(w / 5), int(4 * w / 5))
            x3 = random.randint(int(4 * w / 5), w)
            y1 = random.randint(0, int(2 * h / 5))
            y2 = random.randint(int(2 * h / 5), h)
            y3 = random.randint(0, int(2 * h / 5))

            points = [x1, y1, x2, y2, x3, y3]
            draw = aggdraw.Draw(image)
            # 2 is the outlinewidth in pixels
            color = random_color(10, 200, random.randint(220, 225))
            outline = aggdraw.Pen(color, 5)
            # the pathstring: c for bezier curves (all lowercase letters for relative path)
            pathstring = "c"
            coord_len = len(points)
            for coord in points:
                if points.index(coord) == (coord_len - 1):
                    pathstring += str(coord)
                else:
                    pathstring += str(coord) + " "

            # xy position to place symbol
            xy = (x1, y1)
            symbol = aggdraw.Symbol(pathstring)
            draw.symbol(xy, symbol, outline)
            draw.flush()

            number -= 1
        return image

    @staticmethod
    def create_noisy_straight_line(image, number):
        w, h = image.size
        while number:
            x1 = random.randint(0, int(w / 5))
            x2 = random.randint(int(w / 5), w)
            y1 = random.randint(0, h - int(h / 5))
            y2 = random.randint(y1, h - int(h / 5))

            points = [x1, y1, x2, y2]
            draw = aggdraw.Draw(image)
            color = random_color(10, 200, random.randint(220, 225))
            outline = aggdraw.Pen(color, 5)
            draw.line(points, outline)
            draw.flush()

            number -= 1
        return image

    def create_captcha_image(self, chars, background):
        image = Image.new('RGB', (self._width, self._height), background)
        """mode RGB 3x8-bit pixels, true color
            size 2 tuple, containing (width, height) in pixels
            color = background"""
        draw = Draw(image)

        # degree = random.uniform(-30, 30)

        def draw_character(c):
            font = random.choice(self.truefonts)
            w, h = draw.textsize(c, font=font)
            color = random_color(10, 200, random.randint(220, 255))

            # dx = random.randint(0, 4)
            # dy = random.randint(0, 6)
            dx = 0
            dy = 0
            """RGBA 4x8-bit pixels, true color with transparency mask"""
            im = Image.new('RGBA', (w + dx, h + dy))
            Draw(im).text((dx, dy), c, font=font, fill=color)

            # rotate
            im = im.rotate(random.uniform(-30, 30), Image.BILINEAR, expand=1)
            im = im.crop(im.getbbox())
            """getbbox calculates the bounding box of the images"""

            alpha = im.convert('RGBA').split()[-1]
            bg = Image.new('RGBA', im.size, background + (255,))
            bg.paste(im, mask=alpha)

            im = bg

            # wrap
            x = int(dx)
            y = int(dy)
            w2 = w + abs(x)
            h2 = h + abs(y)

            data = (x, y,
                    -x, h2 - y,
                    w2 + x, h2 + y,
                    w2 - x, -y)

            im = im.resize((w2, h2))
            im = im.transform((w, h), Image.QUAD, data)
            """(w, h) the noisy size
                Image.QUAD the transformation method -> data"""
            return im

        images = []
        for c in chars:
            images.append(draw_character(c))

        text_width = sum([im.size[0] for im in images])

        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        average = int(text_width / len(chars))
        offset = int(average * 0.1)

        for im in images:
            w, h = im.size
            image.paste(im, (offset, int((self._height - h) / 2)), mask=None)
            """paste another images into an images
                offset = x coordinate in upper left
                int((self._height - h) / 2)) = y coordinate in upper left
                box = (x, y)"""
            offset = offset + w

        if width > self._width:
            image = image.resize((self._width, self._height))

        return image

    def generate_image(self, chars):
        background = random_color(238, 255)
        im = self.create_captcha_image(chars, background)
        self.create_noisy_dots(im, number=400)
        self.create_noisy_circles(im, number=random.randint(10, 20))
        self.create_noisy_triangle(im, number=random.randint(5, 10))
        self.create_noisy_straight_line(im, number=random.randint(2, 3))
        self.create_noisy_curve(im, number=random.randint(2, 3))
        im = im.filter(ImageFilter.SMOOTH)
        return im


def random_color(start, end, opacity=None):
    red = random.randint(start, end)
    green = random.randint(start, end)
    blue = random.randint(start, end)
    if opacity is None:
        return red, green, blue
    return red, green, blue, opacity


def random_string():
    random_letters = (random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return "".join(random_letters)


captcha = random_string().encode()

img = ImageCaptcha(fonts=[DEFAULT_FONTS])

created_date = datetime.now().strftime("%c")
converted_date = int(datetime.strptime(created_date, "%c").timestamp())
image_name = "noisy_captcha_" + str(converted_date) + ".png"
abs_image_path = os.path.join(IMAGE_DIR, os.path.join('noisy', image_name))
print(abs_image_path)
hashed_captcha = bcrypt.hashpw(captcha, bcrypt.gensalt())

img_captcha = ImgCaptcha(
    captcha_text=hashed_captcha.decode(),
    image_url=abs_image_path,
    style="noisy shapes and noisy curves captcha",
    created_date=created_date,
).save()

img.write(captcha.decode(), abs_image_path)
