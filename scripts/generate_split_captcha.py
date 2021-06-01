import os
import random
import string
import bcrypt
from PIL import Image, ImageFilter
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from io import BytesIO
from datetime import datetime
from captcha_web_services.models import ImgCaptcha

import django
os.environ["DJANGO_SETTINGS_MODULE"] = "generate_captcha.settings"
django.setup()

DIR = '/home/hanh/Desktop/generate/generate_captcha/'
DATA_DIR = os.path.join(DIR, 'data')
FONTS = os.listdir(os.path.join(DATA_DIR, 'fonts'))
IMAGE_DIR = os.path.join(DIR, 'images')
FONT_SIZE = [64, 68]

DEFAULT_FONTS = []
for font in FONTS:
    DEFAULT_FONTS.append(os.path.join(os.path.join(DATA_DIR, 'fonts'), font))


class Captcha(object):
    def write(self, chars, output, format='png'):
        im = self.generate_image(chars)
        return im.save(output, format=format)


class ImageCaptcha(Captcha):
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
            truetype(n, random.choice(FONT_SIZE))
            for n in self._fonts
        ])
        return self._truefonts

    @staticmethod
    def draw_grid(image, background, line_width=4):
        w, h = image.size
        line_color = background

        # draw grid
        x_start = 0
        x_end = w
        y_start = 0
        y_end = h

        step_width_size = int(w / random.randint(5, 8))
        step_height_size = int(h / random.randint(3, 5))

        draw = Draw(image)

        for x in range(0, w, step_width_size):
            xy = ((x, y_start), (x, y_end))
            draw.line(xy, fill=line_color, width=line_width)

        for y in range(0, h, step_height_size):
            xy = ((x_start, y), (x_end, y))
            draw.line(xy, fill=line_color, width=line_width)

        return image

    def create_captcha_image(self, chars, background):
        image = Image.new('RGBA', (self._width, self._height), background)
        draw = Draw(image)

        def draw_character(c):
            font = random.choice(self.truefonts)
            w, h = draw.textsize(c, font=font)
            color = random_color(10, 200, random.randint(220, 225))

            x = 0
            y = 0

            outline_color = random_color(10, 200, random.randint(220, 225))
            border_width = 2

            im = Image.new('RGBA', (w + border_width, h + border_width))

            Draw(im).text((x - border_width, y), c, font=font, fill=outline_color)
            Draw(im).text((x, y - border_width), c, font=font, fill=outline_color)
            Draw(im).text((x + border_width, y), c, font=font, fill=outline_color)
            Draw(im).text((x, y + border_width), c, font=font, fill=outline_color)

            Draw(im).text((x + border_width, y - border_width), c, font=font, fill=outline_color)
            Draw(im).text((x - border_width, y - border_width), c, font=font, fill=outline_color)
            Draw(im).text((x - border_width, y + border_width), c, font=font, fill=outline_color)
            Draw(im).text((x + border_width, y + border_width), c, font=font, fill=outline_color)

            Draw(im).text((x, y), c, font=font, fill=color)

            im = im.rotate(random.uniform(-30, 30), Image.BILINEAR, expand=1)
            im = im.crop(im.getbbox())

            # remove transparency
            alpha = im.convert('RGBA').split()[-1]
            bg = Image.new('RGBA', im.size, background + (255,))
            bg.paste(im, mask=alpha)

            # bg.save('bg.png', format='png')
            im = bg

            # wrap
            data = (x, y,
                    -x, h - y,
                    w + x, h + y,
                    w - x, -y)

            im = im.resize((w, h))
            im = im.transform((w, h), Image.QUAD, data)
            return im

        images = []
        for c in chars:
            images.append(draw_character(c))

        text_width = sum([im.size[0] for im in images])
        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        average = int(text_width / len(chars))
        offset = int(average * 0.1) + 5

        for im in images:
            w, h = im.size
            image.paste(im, (offset, int((self._height - h) / 2)), mask=None)
            offset += w

        if width > self._width:
            image = image.resize((self._width, self._height))
        return image

    def generate_image(self, chars):
        background = random_color(238, 255)
        im = self.create_captcha_image(chars, background)
        self.draw_grid(im, background)
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
    random_letter = (random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return ''.join(random_letter)


captcha = random_string().encode()
# print(captcha)

img = ImageCaptcha(fonts=[random.choice(DEFAULT_FONTS)])

created_date = datetime.now().strftime("%c")
converted_date = int(datetime.strptime(created_date, "%c").timestamp())
image_name = "split_captcha_" + str(converted_date) + ".png"
abs_image_path = os.path.join(IMAGE_DIR, os.path.join('split', image_name))
print(abs_image_path)
hashed_captcha = bcrypt.hashpw(captcha, bcrypt.gensalt())

img_captcha = ImgCaptcha(
    captcha_text=hashed_captcha.decode(),
    # captcha_text=captcha.decode(),
    image_url=abs_image_path,
    style="split captcha",
    created_date=created_date,
    validated=False,
).save()

img.write(captcha.decode(), abs_image_path)
