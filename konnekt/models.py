# /konnekt/models.py

from django.db import models
from django.utils.translation import gettext_lazy as lazy
import secrets, string
from django.utils import timezone


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
    attachment = models.FileField(blank=True, null=True)
    attachment_type = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']


class MessageImage(models.Model):
    message = models.ForeignKey(ConversationItem, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    image = models.ImageField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    msgID = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.image}"


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


class Contact(models.Model):
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='contacts')
    contact = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='saved_by')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('owner', 'contact')

    def __str__(self):
        return f'{self.owner} saved {self.contact}'



class UserStatus(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(default=timezone.now)
    last_ping = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.username}: {'Online' if self.is_online else 'Offline'}"


class ConversationReadStatus(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    last_read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ('conversation', 'user')


class PushSubscription(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    endpoint = models.TextField(unique=True, null=True)
    keys = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = lazy('Push Subscription')
        verbose_name_plural = lazy('Push Subscriptions')

    def __str__(self):
        return f"Push subscription for {self.user}"
