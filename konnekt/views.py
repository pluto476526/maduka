from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, update_session_auth_hash
from dash.models import Profile
from konnekt.models import Conversation, ConversationItem, Note, Task, Contact, ConversationReadStatus, MessageImage, PushSubscription
import logging
import secrets
import string


logger = logging.getLogger(__name__)
User = get_user_model()


@login_required
def get_vapid_public_key(request):
    return JsonResponse({'vapidPublicKey': settings.VAPID_PUBLIC_KEY})


@csrf_exempt
@login_required
def save_subscription(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        logger.debug(f'data register: {data}')
        PushSubscription.objects.update_or_create(
            user=request.user,
            defaults={'subscription_data': data}
        )
        return JsonResponse({'status': 'subscription saved'})
    return JsonResponse({'error': 'Invalid method'}, status=400)



@csrf_exempt
@login_required
def upload_attachment(request):
    if request.method == 'POST' and request.FILES.getlist('file'):
        uploaded_files = request.FILES.getlist('file')
        msgID = request.POST.getlist('msgID')
        image_urls = []
        file_urls = []
        attachment_type = None

        for file in uploaded_files:
            main_type = file.content_type.split('/')[0]

            # Temporarily store files without creating ConversationItem
            if main_type == 'image':
                msg_img = MessageImage(image=file)
                msg_img.msgID = msgID
                msg_img.save()
                image_urls.append(msg_img.image.url)
                attachment_type = 'image'
            else:
                file_urls.append(file.url)
                attachment_type = main_type

        return JsonResponse({
            'image_urls': image_urls,
            'file_urls': file_urls,
            'attachment_type': attachment_type,
            'uniqueMsgID': msgID,
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_user_func(request):
    query = request.GET.get('qq', '')
    logger.debug(f"Search query: {query}")  # Debugging

    if query:
        try:
            results = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
            results_list = list(results.values('id', 'username', 'profile__avatar', 'profile__identifier'))
            for result in results_list:
                result['avatar_url'] = result['profile__avatar']

            logger.debug(f"Results: {results_list}")  # Debugging
            return JsonResponse({'results': results_list})
        except Exception as e:
            logger.debug(f"Error: {e}")  # Print any errors
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'results': []})


@login_required
def index_view(request):
    if request.method == 'POST':
        source = request.POST.get('source')
        note = request.POST.get('note')
        noteID = request.POST.get('noteID')
        task = request.POST.get('task')
        taskID = request.POST.get('taskID')
        userID = request.POST.get('userID')

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
        
        elif source == 'new_contact':
            contact = User.objects.get(id=userID)
            s_contact = Contact.objects.filter(owner=request.user, contact=contact).first()
            
            if s_contact:
                messages.error(request, f'{contact} is already in your contacts list.')
                return redirect(request.META.get('HTTP_REFERER'))
            
            Contact.objects.create(owner=request.user, contact=contact)
            messages.success(request, f'{contact} added to your contacts list.')

        elif source == 'new_convo':
            friend = User.objects.get(id=userID)
            old_convo = Conversation.objects.filter(is_group=False, participants=request.user).filter(participants=friend).first()
            
            if old_convo:
                return redirect('chat_view', old_convo.conv_id)

            convo = Conversation.objects.create(is_group=False)
            convo.participants.set([request.user, friend])
            convo.save
            return redirect('chat_view', convo.conv_id)

        return redirect(request.META.get('HTTP_REFERER'))
    
    context = {}
    return render(request, 'konnekt/index.html', context)


@login_required
def chat_view(request, convo_id):
    convo = get_object_or_404(Conversation, conv_id=convo_id)
    r_statuses = ConversationReadStatus.objects.filter(conversation=convo)
    texts = ConversationItem.objects.filter(conversation=convo)
    participants = []

    if convo.is_group:
        p = convo.participants.exclude(id=request.user.id).first()
        participants.append(p)
    
    else:
        sender = convo.participants.exclude(id=request.user.id).first()
        contact = Contact.objects.filter(owner=request.user, contact=sender).exists()
    
    context = {
        'texts': texts,
        'convo_id': convo_id,
        'convo': convo,
        'sender': sender,
        'contact': contact,
        'r_statuses': r_statuses,
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
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
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

                case 'change_password':        
                    user = request.user

                    if not user.check_password(current_password):
                        messages.error(request, 'Current password is incorrect.')
                        return redirect('my_profile')

                    if new_password != confirm_password:
                        messages.error(request, 'New passwords do not match.')
                        return redirect('my_profile')

                    if len(new_password) < 8:
                        messages.error(request, 'New password must be at least 8 characters long.')
                        return redirect('my_profile')

                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)  # Keep user logged in
                    messages.success(request, 'Your password has been successfully changed.')


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



