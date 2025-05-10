from django.contrib import admin
from konnekt.models import PushSubscription, Conversation, ConversationItem, ConversationReadStatus, Note, Task, UserStatus

admin.site.register(Conversation)
admin.site.register(ConversationItem)
admin.site.register(Task)
admin.site.register(UserStatus)
admin.site.register(Note)
admin.site.register(ConversationReadStatus)
admin.site.register(PushSubscription)
