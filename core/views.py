from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.core import management
from django.views.decorators.csrf import csrf_exempt
from decouple import config


@csrf_exempt
def deploy(request, token):
    expected = config('DEPLOY_TOKEN', default='')
    if not expected or token != expected:
        return HttpResponseForbidden('Invalid token')

    management.call_command('deploy')
    return HttpResponse('OK')
