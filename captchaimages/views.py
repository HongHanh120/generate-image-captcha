import sys
import requests
import simplejson
from rest_framework_mongoengine import viewsets
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from .serializers import CaptchaImageSerializer
from django.core.exceptions import ObjectDoesNotExist
from subprocess import run, PIPE

from .models import *
from scripts.generate_mass_captcha import *


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
               '//home//hanh//Desktop//generate//generate_captcha//scripts//generate_mass_captcha.py'],
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
        # print(image_dict)
        data = {
            'remote_id': image_dict['id'],
            'remote_url': image_dict['image_url'],
        }
        return JsonResponse({'data': data}, safe=False)
    else:
        return JsonResponse({'data': {}}, safe=False)


def check_response(request):
    if request.method == "POST":
        data = json.loads(request.body)
        response = data['response']
        print(response)

        id_image = data['remote_image_id']
        image = ImgCaptcha.objects(id=id_image)
        serializer = CaptchaImageSerializer(image, many=True)
        image_dict = json.loads(json.dumps(serializer.data))[0]
        print(image_dict['captcha_text'])

        if image_dict['captcha_text'] == response:
            result = 'Success'
        else:
            result = 'Fail'
        print(result)
        return JsonResponse({'data': result})
