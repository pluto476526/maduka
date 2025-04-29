from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from dash.models import Profile
from konnekt.models import Conversation, ConversationItem, Note, Task
import logging


logger = logging.getLogger(__name__)



@login_required
def index_view(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        note = request.POST.get('note')
        noteID = request.POST.get('noteID')
        task = request.POST.get('task')
        taskID = request.POST.get('taskID')

        if source == 'add_note':
            Note.objects.create(user=request.user, note=note)
            messages.success(request, 'Note saved.')
        
        elif source == 'delete_note':
            note = get_object_or_404(Note, id=noteID)
            note.is_deleted = True
            note.save()
            messages.success(request, 'Note deleted.')

        elif source == 'add_task':
            Task.objects.create(user=request.user, task=task)
            messages.success(request, 'Task added.')

        elif source == 'complete_task':
            task = get_object_or_404(Task, id=taskID)
            task.is_complete = True
            task.save()
            messages.success(request, 'Task completed.')

        elif source == 'delete_task':
            task = get_object_or_404(Task, id=taskID)
            task.is_deleted = True
            task.save()
            messages.success(request, 'Task deletd.')

        return redirect(request.META.get('HTTP_REFERER'))
    
    context = {}
    return render(request, 'konnekt/index.html', context)


@login_required
def chat_view(request, convo_id):
    convo = get_object_or_404(Conversation, conv_id=convo_id)
    texts = ConversationItem.objects.filter(conversation=convo)
    logger.debug(convo.participants)
    participants = []

    if convo.is_group:
        p = convo.participants.exclude(id=request.user.id).first()
        participants.append(p)
    
    else:
        sender = convo.participants.exclude(id=request.user.id).first()

    context = {
        'texts': texts,
        'convo_id': convo_id,
        'convo': convo,
        'sender': sender,
    }
    return render(request, 'konnekt/chat.html', context)


@login_required
def my_profile_view(request):
    profile = get_object_or_404(Profile, id=request.user.profile.id)
    
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
    return render(request, 'konnekt/my_profile.html', context)


def user_profile_view(request, identifier):
    profile = get_object_or_404(Profile, identifier=identifier)
    context = {
        'profile': profile,
    }
    return render(request, 'konnekt/user_profile.html', context)



