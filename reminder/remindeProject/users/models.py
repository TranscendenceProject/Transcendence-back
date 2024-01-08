from django.db import models
import secrets

# Create your models here.

class UserProfile(models.Model):
    external_id = models.CharField(max_length=100, unique=True)  # 외부 사이트 아이디
    external_name = models.CharField(max_length=100, unique=True, null=True)
    profile_picture = models.URLField()  # 프로필 사진 URL
    otp_number = models.CharField(max_length=6, null=True)  # OTP 숫자 필드 추가

    def __str__(self):
        return self.external_id

