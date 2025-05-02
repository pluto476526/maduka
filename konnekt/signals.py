# app/signals.py
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.utils import timezone

@receiver(user_logged_out)
def set_user_offline(sender, request, user, **kwargs):
    if hasattr(user, 'profile'):
        profile = user.profile
        profile.is_online = False
        profile.last_seen = timezone.now()
        profile.save()

