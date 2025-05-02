from django.contrib import admin
from konnekt.models import Conversation, ConversationItem, Note, Task, UserStatus

admin.site.register(Conversation)
admin.site.register(ConversationItem)
admin.site.register(Task)
admin.site.register(UserStatus)
admin.site.register(Note)
