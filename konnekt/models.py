from django.db import models
import secrets, string


class Conversation(models.Model):
    conv_id = models.CharField(max_length=8, unique=True, editable=False)
    is_group = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True)  # Only for group chats
    participants = models.ManyToManyField('auth.User', related_name='conversations')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']

    def save(self, *args, **kwargs):
        if not self.conv_id:
            self.conv_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(20))
        super().save(*args, **kwargs)

    def __str__(self):
        if self.is_group:
            return self.title or f"Group {self.conv_id}"
        return f"Conversation {self.conv_id}"



class ConversationItem(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.sender} in {self.conversation}"


class Note(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    note = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}'s note"


class Task(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    task = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}: {self.task}"
