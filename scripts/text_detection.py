import os
import json
import cv2
import pytesseract
from pytesseract import Output

DIR = '/home/hanh/Desktop/generate/generate_captcha/scripts'
IMAGES = os.listdir(os.path.join(DIR, 'images'))
MASS_IMAGES = []

for im in IMAGES:
    img_path = os.path.join(os.path.join(DIR, 'images'), im)
    MASS_IMAGES.append(img_path)


# print(MASS_IMAGES)
test_images = []


def write_json(data, filename='data.json'):
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

    for word in details['text']:
        if word != '':
            word_list.append(word)
            last_word = word

        if (last_word != '' and word == '') or (word == details['text'][-1]):
            parse_text.append(word_list)
            word_list = []

    new_data = {
        "images": im,
        "text_detection": parse_text[0],
    }
    # new_data = '\n'.join(new_data)
    test_images.append(new_data)

write_json(test_images)
