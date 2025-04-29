from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta

# =================== MODELS ===================

class InstagramAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    page_id = models.CharField(max_length=255)
    ig_user_id = models.CharField(max_length=255)
    access_token = models.TextField()
    expires_at = models.DateTimeField()


# =================== VIEWS ===================

CLIENT_ID = 'YOUR_APP_ID'
CLIENT_SECRET = 'YOUR_APP_SECRET'
REDIRECT_URI = 'https://yourdomain.com/instagram/callback/'


def instagram_login(request):
    scope = 'instagram_basic, pages_show_list, instagram_content_publish, pages_read_engagement'
    auth_url = f'https://www.facebook.com/v17.0/dialog/oauth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={scope}'
    return redirect(auth_url)


def instagram_callback(request):
    code = request.GET.get('code')
    token_url = 'https://graph.facebook.com/v17.0/oauth/access_token'
    params = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code,
    }
    response = requests.get(token_url, params=params).json()
    access_token = response.get('access_token')
    expires_in = response.get('expires_in', 5184000)  # default to 60 days
    expires_at = datetime.now() + timedelta(seconds=expires_in)

    InstagramAccount.objects.update_or_create(
        user=request.user,
        defaults={
            'access_token': access_token,
            'expires_at': expires_at,
        }
    )
    return redirect('instagram_get_pages')


def instagram_get_pages(request):
    ig_account = InstagramAccount.objects.get(user=request.user)
    token = ig_account.access_token
    res = requests.get(f'https://graph.facebook.com/me/accounts?access_token={token}')
    pages = res.json().get('data')
    return render(request, 'instagram/pages.html', {'pages': pages})


def instagram_get_ig_account(request, page_id):
    ig_account = InstagramAccount.objects.get(user=request.user)
    token = ig_account.access_token
    url = f'https://graph.facebook.com/v17.0/{page_id}?fields=instagram_business_account&access_token={token}'
    response = requests.get(url).json()
    ig_user_id = response['instagram_business_account']['id']

    InstagramAccount.objects.filter(user=request.user).update(
        page_id=page_id,
        ig_user_id=ig_user_id
    )
    return redirect('instagram_get_media', ig_user_id=ig_user_id)


def instagram_get_media(request, ig_user_id):
    ig_account = InstagramAccount.objects.get(user=request.user)
    token = ig_account.access_token
    url = f'https://graph.facebook.com/v17.0/{ig_user_id}/media'
    params = {
        'fields': 'id,caption,media_type,media_url,permalink,timestamp',
        'access_token': token
    }
    media = requests.get(url, params=params).json()
    return render(request, 'instagram/media.html', {'media': media, 'ig_user_id': ig_user_id})


@csrf_exempt
def instagram_post_image(request):
    if request.method == 'POST':
        ig_user_id = request.POST.get('ig_user_id')
        image_url = request.POST.get('image_url')
        caption = request.POST.get('caption')
        ig_account = InstagramAccount.objects.get(user=request.user)
        token = ig_account.access_token

        creation = requests.post(f'https://graph.facebook.com/v17.0/{ig_user_id}/media', data={
            'image_url': image_url,
            'caption': caption,
            'access_token': token,
        }).json()

        creation_id = creation.get('id')

        publish = requests.post(f'https://graph.facebook.com/v17.0/{ig_user_id}/media_publish', data={
            'creation_id': creation_id,
            'access_token': token,
        }).json()

        return redirect('instagram_get_media', ig_user_id=ig_user_id)
    return JsonResponse({'error': 'POST required'})


# =================== URLS ===================

from django.urls import path

urlpatterns = [
    path('instagram/login/', instagram_login, name='instagram_login'),
    path('instagram/callback/', instagram_callback, name='instagram_callback'),
    path('instagram/pages/', instagram_get_pages, name='instagram_get_pages'),
    path('instagram/<str:page_id>/account/', instagram_get_ig_account, name='instagram_get_ig_account'),
    path('instagram/<str:ig_user_id>/media/', instagram_get_media, name='instagram_get_media'),
    path('instagram/post/', instagram_post_image, name='instagram_post_image'),
]
