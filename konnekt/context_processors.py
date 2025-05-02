from django.contrib.auth import get_user_model
from konnekt.models import Conversation, ConversationItem, Note, Task, Contact
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def get_notes(request):
    if not request.user.is_authenticated:
        return {}

    notes = Note.objects.filter(user=request.user, is_deleted=False)
    return {'notes': notes}


def get_tasks(request):
    if not request.user.is_authenticated:
        return {}

    tasks = Task.objects.filter(user=request.user, is_deleted=False)
    return {'tasks': tasks}


def get_all_users(request):
    if not request.user.is_authenticated:
        return {}

    registered_users = get_user_model().objects.order_by('username')
    return {'registered_users': registered_users}


def get_contacts(request):
    if not request.user.is_authenticated:
        return {}

    # contacts = request.user.contacts.exclude(is_deleted=True).order_by('contact')
    g_contacts = defaultdict(list)
    contacts = request.user.contacts.exclude(is_deleted=True).select_related('contact__profile', 'contact__status').order_by('contact__username')

    for c in contacts:
        first_letter = c.contact.username[0].upper()
        g_contacts[first_letter].append(c)

    s_contacts = sorted(g_contacts.items())
    for s in s_contacts:
        logger.debug('>>>>>>> last seen')
        logger.debug(s)
    return {'contacts': s_contacts}
