from django.db import models

class Conversation(models.Model):
    convID = models.CharField(max_length=20, unique=True, editable=False)
    is_group = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True)  # Only for group chats
    participants = models.ManyToManyField('auth.User', related_name='conversations')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.convID:
            self.convID = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_group:
            return self.title or f"Group {self.convID}"
        return f"Conversation {self.convID}"



class ConversationItem(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} in {self.conversation}"

