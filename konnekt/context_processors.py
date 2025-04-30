from konnekt.models import Conversation, ConversationItem, Note, Task


def get_notes(request):
    if not request.user.is_authenticated:
        return {}

    # Fetch users notes
    notes = Note.objects.filter(user=request.user, is_deleted=False)
    return {'notes': notes}


def get_tasks(request):
    if not request.user.is_authenticated:
        return {}

    # Fetch users tasks
    tasks = Task.objects.filter(user=request.user, is_deleted=False)
    return {'tasks': tasks}


