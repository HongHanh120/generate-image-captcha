import json
from mongoengine import *
from datetime import datetime


# Create your models here.
class ImgCaptcha(Document):
    captcha_text = StringField(max_length=255, unique=True, required=True)
    image_url = StringField(unique=True, required=True)
    style = StringField(max_length=255, required=True)
    created_date = DateTimeField(requied=True)

    def json(self):
        captcha_dict = {
            "captcha_text": self.captcha_text,
            "image_url": self.image_url,
            "style": self.style,
            "created_date": self.created_date,
        }
        return json.dumps(captcha_dict)

    meta = {
        "indexes": ["captcha_text"],
        "ordering": ["-created_date"],
    }

# captcha = ImgCaptcha(
#     captcha_text="$2b$12$pz2324Ym9XnrIfI0dC1ciO.qm5pj9RUYOYg0b./rVEwMZQfBV9Gi",
#     image_url="/home/hanh/Desktop/captcha/images/mass/mass_captcha_1617305530.png",
#     style="mass_captcha",
#     created_date=datetime.timestamp(datetime.utcnow()),
# ).json()
# print(captcha)

# for captcha in ImgCaptcha.objects:
#     print(captcha.image_url)
