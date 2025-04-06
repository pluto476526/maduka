from django.db import models
import secrets
import string


class MainHelpDesk(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.SET_NULL, null=True)
    username = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='user')
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    issue = models.CharField(max_length=100)
    description = models.TextField()
    help_id = models.CharField(max_length=10, unique=True, blank=True, null=True)
    status = models.CharField(max_length=10, default='pending')
    admin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True, related_name='superadmin')
    is_sorted = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.shop}: {self.issue}'

    def save(self, *args, **kwargs):
        if not self.help_id:
            self.help_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        super().save(*args, **kwargs)


class Notification(models.Model):
    shop = models.ForeignKey('shop.Shop', on_delete=models.CASCADE)
    origin = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    n_type = models.CharField(max_length=10, null=True) # alert, warning, error, success
    message = models.CharField(max_length=255)
    target = models.CharField(max_length=10, null=True) # superadmin, admin, everyone
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.shop}: {self.origin}'
