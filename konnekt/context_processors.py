from konnekt.models import Conversation, ConversationItem, Note, Task

def get_recent_chats(request):
    if not request.user.is_authenticated:
        return {}

    # Fetch all conversations the user is a part of
    convos = Conversation.objects.filter(participants=request.user).distinct()
 
    # Fetch the first participant (excluding the current user) for each conversation
    participants = []
    last_messages = []

    for c in convos:
        # Get the first participant (not the current user)
        participant = c.participants.exclude(id=request.user.id).first()
        participants.append(participant)

        # Get the last message in the conversation
        last_message = c.messages.order_by('-timestamp').first()
        last_messages.append(last_message)

    # Combine the conversations, participants, and last messages into a list of tuples
    z_data = zip(convos, participants, last_messages)
    return {'z_data': z_data} 


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


