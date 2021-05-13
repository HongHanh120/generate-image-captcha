from django.urls import include, path
from rest_framework import routers
from django.views.decorators.csrf import csrf_exempt

from . import views

router = routers.DefaultRouter()
router.register(r'captcha_web_services', views.ImgCaptchaViewSet, 'captcha_image')

urlpatterns = [
    path('', include(router.urls)),
    path('captcha/', views.captcha_image_list),
    path('captcha/<str:pk>/', views.captcha_image_detail),
    path('api/generate-image/', views.generate_image_captcha),
    path('api/check-answer/', csrf_exempt(views.check_answer))
]
