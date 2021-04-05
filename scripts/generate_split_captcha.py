import os
import random
import string
from PIL import Image, ImageFilter
from PIL.ImageDraw import Draw
from PIL.ImageFont import truetype
from io import BytesIO
from datetime import datetime

# from db.models import ImgCaptcha

DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
DEFAULT_FONTS = [os.path.join(DATA_DIR, 'DroidSansMono.ttf')]
FONT_SIZE = 70

table = []
for i in range(256):
    table.append(i)


class Captcha(object):
    def generate(self, chars, format='png'):
        im = self.generate_image(chars)
        out = BytesIO()
        im.save(out, format=format)
        out.seek(0)
        return out

    def write(self, chars, output, format='png'):
        im = self.generate_image(chars)
        return im.save(output, format=format)


class ImageCaptcha(Captcha):
    def __init__(self, width=270, height=90, fonts=None, font_sizes=None):
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
        return self._truefonts

    @staticmethod
    def draw_grid(image, line_width=4):
        w, h = image.size
        line_color = (255, 255, 255)

        # draw grid
        x_start = 0
        x_end = w
        y_start = 0
        y_end = h

        step_width_size = int(w / 7)
        step_height_size = int(h / 4)

        draw = Draw(image)

        for x in range(0, w, step_width_size):
            xy = ((x, y_start), (x, y_end))
            draw.line(xy, fill=line_color, width=line_width)

        for y in range(0, h, step_height_size):
            xy = ((x_start, y), (x_end, y))
            draw.line(xy, fill=line_color, width=line_width)

        return image

    def create_captcha_image(self, chars, color, background):
        image = Image.new('RGBA', (self._width, self._height), background)
        draw = Draw(image)

        def draw_character(c):
            font = random.choice(self.truefonts)
            w, h = draw.textsize(c, font=font)

            dx = 0
            dy = 0

            # outline_color = (128, 128, 128)
            # border_width = 2

            im = Image.new('RGBA', (w, h))

            # Draw(im).text((dx - border_width, dy), c, font=font, fill=outline_color)
            # Draw(im).text((dx, dy - border_width), c, font=font, fill=outline_color)
            # Draw(im).text((dx + border_width, dy), c, font=font, fill=outline_color)
            # Draw(im).text((dx, dy + border_width), c, font=font, fill=outline_color)
            #
            # Draw(im).text((dx + border_width, dy - border_width), c, font=font, fill=outline_color)
            # Draw(im).text((dx - border_width, dy - border_width), c, font=font, fill=outline_color)
            # Draw(im).text((dx - border_width, dy + border_width), c, font=font, fill=outline_color)
            # Draw(im).text((dx + border_width, dy + border_width), c, font=font, fill=outline_color)

            Draw(im).text((dx, dy), c, font=font, fill=color)

            im = im.rotate(random.uniform(-30, 30), Image.BILINEAR, expand=1)
            im = im.crop(im.getbbox())

            # remove transparency 1
            # datas = im.getdata()
            #
            # newData = []
            # for item in datas:
            #     if item[0] == color[0] and item[1] == color[1] and item[2] == color[2]:
            #         newData.append(item)
            #     else:
            #         newData.append(background)
            #
            # im.putdata(newData)

            # remove transparency 2
            alpha = im.convert('RGBA').split()[-1]
            bg = Image.new('RGBA', im.size, background + (255,))
            bg.paste(im, mask=alpha)

            # bg.save('bg.png', format='png')
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
            return im

        images = []
        for c in chars:
            images.append(draw_character(c))

        text_width = sum([im.size[0] for im in images])
        width = max(text_width, self._width)
        image = image.resize((width, self._height))

        average = int(text_width / len(chars))
        offset = int(average * 0.1) + 5

        # count = 0
        for im in images:
            w, h = im.size
            # mask = im.convert('L').point(table)
            # mask_im_blur = mask.filter(ImageFilter.GaussianBlur(5))
            # im.save("mask_" + str(count) + '.png', format='png')
            image.paste(im, (offset, int((self._height - h) / 2)), mask=None)
            offset += w
            # count += 1

        if width > self._width:
            image = image.resize((self._width, self._height))
        return image

    def generate_image(self, chars):
        background = (212, 212, 212)
        text_color = (0, 0, 0)
        im = self.create_captcha_image(chars, text_color, background)
        self.draw_grid(im)
        im = im.filter(ImageFilter.SMOOTH)
        return im


def random_string():
    random_letter = (random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return ''.join(random_letter)


captcha = random_string()
print(captcha)

img = ImageCaptcha(fonts=['/home/hanh/Desktop/captcha/data/fonts/DroidSansMono.ttf'])

created_date = datetime.now().strftime("%c")
converted_date = int(datetime.strptime(created_date, "%c").timestamp())
image_name = "split_captcha_" + str(converted_date) + ".png"
image_dir = '/home/hanh/Desktop/captcha/images/split'
abs_image_path = os.path.join(image_dir, image_name)
print(abs_image_path)
img.write(captcha, abs_image_path)

# img_captcha = ImgCaptcha(
#     captcha_text=captcha,
#     url_image=abs_image_path,
#     style_captcha="split_captcha",
#     created_date=created_date,
# ).save()
