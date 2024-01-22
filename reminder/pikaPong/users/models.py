from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Django 에서 기본 제공하는 user
    intra_pk_id = models.CharField(max_length=100, unique=True) # 42seoul PK value
    intra_id = models.CharField(max_length=100, null=True, blank=True) # 42seoul nickname
    nick_name = models.CharField(max_length=100, null=True, blank=True) # game nickname
    profile_picture = models.URLField(blank=True) # 42seoul profile
    otp_number = models.CharField(max_length=6, null=True, blank=True)
    bio = models.TextField(blank=True, default="")  # About me

    def __str__(self):
        return self.user.username

# 자동으로 UserProfile 생성 및 업데이트
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()
