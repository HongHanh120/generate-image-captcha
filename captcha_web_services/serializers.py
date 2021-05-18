from rest_framework_mongoengine import serializers
from .models import *


class CaptchaImageSerializer(serializers.DocumentSerializer):
    class Meta:
        model = ImgCaptcha
        fields = ['id', 'captcha_text', 'image_url', 'style', 'created_date', 'validated']


# serializer = CaptchaImageSerializer(captcha)
# print(serializer.data)
