import json
import random
import string
from datetime import datetime
import math
import numpy as np

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request, "home.html")

def email(subject, message, recipient_list):
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient_list)

@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        body = json.loads(request.body)
        name = body['name']
        phone = body['phone']
        user_email = body['email']
        message = body['message']
        message = "Name:{}. Phone:{}. Email:{}. Message:{}".format(name, phone, user_email, message)
        email("Registration Completed", message, ["inquiry@revecy.com"])
        return JsonResponse({"message":"only POST request is entertained"})

def visualization(request):
    return render(request, "visualization.html")
