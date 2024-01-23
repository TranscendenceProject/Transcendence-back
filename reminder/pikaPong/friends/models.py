from django.db import models
from users.models import UserProfile  # UserProfile 모델 임포트

class Friend(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='friends')
    friend_name = models.CharField(max_length=100)
    # 추가 필드 정의 가능

    def __str__(self):
        return self.friend_name
