from django.db import models
from django.db.models import JSONField

class UserProfile(models.Model):
    intra_pk_id = models.CharField(max_length=100, unique=True, primary_key=True) # 42seoul PK value
    intra_id = models.CharField(max_length=100, null=True, blank=True) # 42seoul nickname
    nick_name = models.CharField(max_length=100, null=True, blank=True) # game nickname
    profile_picture = models.URLField(blank=True) # 42seoul profile
    otp_number = models.CharField(max_length=6, null=True, blank=True)
    bio = models.TextField(blank=True, default="")  # About me
    histories = JSONField(default=list)


    def __str__(self):
        return self.intra_id