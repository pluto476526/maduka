from django.contrib import admin
from konnekt.models import Conversation, ConversationItem, Note, Task

admin.site.register(Conversation)
admin.site.register(ConversationItem)
admin.site.register(Task)
admin.site.register(Note)
