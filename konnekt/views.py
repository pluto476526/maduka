from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from dash.models import Profile
import logging


logger = logging.getLogger(__name__)


@login_required
def index_view(request):
    convos = Coversation.items.filter
    context = {}
    return render(request, 'chats/index.html', context)


@login_required
def my_profile_view(request):
    profile = get_object_or_404(Profile, identifier=request.user.profile.identifier)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip().lower()
        phone = request.POST.get('phone', '')
        # email = request.POST.get('email', '')
        facebook = request.POST.get('facebook', '')
        insta = request.POST.get('insta', '')
        twitter = request.POST.get('twitter', '')
        avatar = request.FILES.get('avatar', '')
        bio = request.POST.get('bio', '')
        source = request.POST.get('source')

        with transaction.atomic():
            match source:
                
                case 'edit_avatar':
                    profile.avatar = avatar
                    profile.save()
                    messages.success(request, 'Profile picture updated.')
                
                case 'edit_profile':
                    profile.full_name = full_name
                    profile.phone = phone
                    profile.facebook = facebook
                    profile.insta = insta
                    profile.twitter = twitter
                    profile.bio = bio
                    if avatar:
                        profile.avatar = avatar
                    profile.save()
                    messages.success(request, 'Profile details updated.')

        return redirect('my_profile')

    context = {
        'my_profile': profile,
    }
    return render(request, 'chats/my_profile.html', context)


def user_profile_view(request):
    context = {}
    return render(request, 'chats/user_profile.html', context)
