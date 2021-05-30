import os
import json
import cv2
import pytesseract
import bcrypt
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from pytesseract import Output

from captcha_web_services.models import *
from captcha_web_services.serializers import *

import django
os.environ["DJANGO_SETTINGS_MODULE"] = "generate_captcha.settings"
django.setup()

DIR = '/home/hanh/Desktop/generate/generate_captcha/images'
IMAGES = os.listdir(os.path.join(DIR, 'mass'))
MASS_IMAGES = []

for im in IMAGES:
    img_path = os.path.join(os.path.join(DIR, 'mass'), im)
    MASS_IMAGES.append(img_path)

# print(MASS_IMAGES)
test_images = []


def write_json(data, filename='mass.json'):
    with open(filename, "a") as f:
        f.write('[' + '\n')
        for d in data:
            if d == data[-1]:
                f.write(json.dumps(d))
                f.write('\n')
            else:
                f.write(json.dumps(d))
                f.write(',')
                f.write('\n')
        f.write(']')
        f.write('\n')
        f.close()


for im in MASS_IMAGES:
    image = cv2.imread(im)

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    threshold_img = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # cv2.imshow('threshold image', threshold_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # configuring parameters for tesseract
    custom_config = r'--oem 3 --psm 6'

    details = pytesseract.image_to_data(threshold_img, output_type=Output.DICT, config=custom_config, lang='eng')
    # print(details.keys())

    total_boxes = len(details['text'])

    for sequence_number in range(total_boxes):
        if int(details['conf'][sequence_number]) > 30:
            (x, y, w, h) = (details['left'][sequence_number],
                            details['top'][sequence_number],
                            details['width'][sequence_number],
                            details['height'][sequence_number])
            threshold_img = cv2.rectangle(threshold_img, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # cv2.imshow('captured text', threshold_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # cv2.waitKey(1)

    parse_text = []
    word_list = []
    last_word = ''
    string = ''
    total_text_detection = []
    checked_result = False

    for word in details['text']:
        if word != '':
            word_list.append(word)
            last_word = word

        if (last_word != '' and word == '') or (word == details['text'][-1]):
            parse_text.append(word_list)
            word_list = []

    for list_text in parse_text:
        total_text_detection += list_text

    for text in total_text_detection:
        string += text
    # print(string)

    captcha_image = ''
    try:
        captcha_image = ImgCaptcha.objects(image_url=im)
    except ObjectDoesNotExist:
        print(HttpResponse(status=404))

    serializer = CaptchaImageSerializer(captcha_image, many=True)
    image_dict = json.loads(json.dumps(serializer.data))[0]

    if len(string) == 6:
        if bcrypt.checkpw(bytes(string, 'utf-8'), image_dict['captcha_text'].encode()):
            checked_result = True

    new_data = {
        "images": im,
        "text_detection": parse_text,
        "check_with_captcha_text": checked_result
    }
    if checked_result is True:
        print(new_data)
    # print(new_data)
    test_images.append(new_data)

write_json(test_images)
