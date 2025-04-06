from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    user = models.CharField(max_length=10)
    email = models.EmailField()
    subject = models.CharField(max_length=50)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)



