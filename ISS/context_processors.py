import os
import os.path
import re
import random

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AnonymousUser

from ISS import utils


banners = os.listdir(os.path.join('ISS/static', utils.get_config('banner_dir')))
banners = [x for x in banners if re.match(r'.*\.(gif|png|jpg)', x)]

def banner(request):
    if not banners:
        return ''

    banner_name = random.choice(banners)

    return {
        'banner': os.path.join(utils.get_config('banner_dir'), banner_name)
    }

def forum_config(request):
    return {'config': utils.get_config()}

def user_config(request):
    ctx = {}

    if isinstance(request.user, AnonymousUser):
        ctx['embed_images'] = True
        ctx['login_form'] = AuthenticationForm()
    else:
        ctx['embed_images'] = request.user.embed_images()

    return ctx
