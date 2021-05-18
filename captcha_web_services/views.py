import os
import sys
import bcrypt
import bson
import requests
import random
import simplejson
import dateutil.parser
from bson.errors import InvalidId
from rest_framework_mongoengine import viewsets
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .serializers import CaptchaImageSerializer
from django.core.exceptions import ObjectDoesNotExist
from subprocess import run, PIPE

from .models import *
from scripts.generate_mass_captcha import *
from scripts.generate_split_captcha import *
from scripts.generate_noisy_curves_noisy_shapes_captcha import *

SCRIPTS = [
    '//home//hanh//Desktop//generate//generate_captcha//scripts//generate_mass_captcha.py',
    '//home//hanh//Desktop//generate//generate_captcha//scripts//generate_split_captcha.py',
    '//home//hanh//Desktop//generate//generate_captcha//scripts//generate_noisy_curves_noisy_shapes_captcha.py',
]


# Create your views here.
class ImgCaptchaViewSet(viewsets.ModelViewSet):
    queryset = ImgCaptcha.objects.all().order_by('created_date')
    serializer_class = CaptchaImageSerializer

    def get_queryset(self):
        return ImgCaptcha.objects.all()


@csrf_exempt
def captcha_image_list(request):
    if request.method == "GET":
        captcha_images = ImgCaptcha.objects.all()
        serializer = CaptchaImageSerializer(captcha_images, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == "POST":
        data = JSONParser().parse(request)
        serializer = CaptchaImageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


def captcha_image_detail(request, pk):
    try:
        captcha_image = ImgCaptcha.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = CaptchaImageSerializer(captcha_image)
        print(serializer)
        return JsonResponse(serializer.data)

    elif request.method == 'PUT':
        data = JSONParser().parse(request)
        serializer = CaptchaImageSerializer(captcha_image, data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == 'DELETE':
        captcha_image.delete()
        return HttpResponse(status=204)


def generate_image_captcha(request):
    out = run([sys.executable,
               random.choice(SCRIPTS)],
              shell=False,
              stdout=PIPE)

    url = "".join(map(chr, out.stdout)).split('\n')[0]

    try:
        captcha_image = ImgCaptcha.objects(image_url=url)
    except ObjectDoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        serializer = CaptchaImageSerializer(captcha_image, many=True)
        image_dict = json.loads(json.dumps(serializer.data))[0]

        data = {
            'remote_id': image_dict['id'],
            'remote_url': image_dict['image_url'],
        }
        return JsonResponse({'data': data}, safe=False)
    else:
        return JsonResponse({'data': {}}, safe=False)


def validate_captcha(request):
    if request.method == "POST":
        requested_time = datetime.now().strftime("%c")
        requested_timestamp = int(datetime.strptime(requested_time, "%c").timestamp())

        data = json.loads(request.body)
        answer = data.get('answer')
        id_image = data.get('remote_image_id')

        if answer is None:
            result = 'fail'
            error_code = 'missing_input_answer'
            response = {
                'result': result,
                'error_code': error_code,
            }
            return JsonResponse({'response': response})
        elif id_image is None:
            result = 'fail'
            error_code = 'missing_input_remote_image_id'
            response = {
                'result': result,
                'error_code': error_code,
            }
            return JsonResponse({'response': response})
        else:
            try:
                image = ImgCaptcha.objects(id=bson.objectid.ObjectId(id_image))
            except (TypeError, InvalidId):
                image = None

            if image is None:
                result = 'fail'
                error_code = 'invalid_input_remote_image_id'
                response = {
                    'result': result,
                    'error_code': error_code,
                }
                return JsonResponse({'response': response})

            if answer is None:
                result = 'fail'
                error_code = 'invalid_input_answer'
                response = {
                    'result': result,
                    'error_code': error_code,
                }
                return JsonResponse({'response': response})

            serializer = CaptchaImageSerializer(image, many=True)
            image_dict = json.loads(json.dumps(serializer.data))[0]

            created_time = dateutil.parser.parse(image_dict['created_date'])
            created_timestamp = int(datetime.strptime(created_time.strftime("%c"), "%c").timestamp())

            if created_timestamp + 120 >= requested_timestamp and image_dict['validated'] is False:
                if bcrypt.checkpw(answer.encode(), image_dict['captcha_text'].encode()):
                    result = 'success'
                    response = {
                        'result': result,
                    }
                else:
                    result = 'fail'
                    error_code = 'incorrect_input_answer'
                    response = {
                        'result': result,
                        'error_code': error_code,
                    }
                image.update(validated=True)
            else:
                result = 'fail'
                error_code = 'timeout_or_duplicate'
                response = {
                    'result': result,
                    'error_code': error_code,
                }
            print(response)
            return JsonResponse({'response': response})
    else:
        return JsonResponse({'response': {}})
