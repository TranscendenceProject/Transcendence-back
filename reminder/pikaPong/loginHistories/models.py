from django.db import models
from django.utils import timezone

class LoginHistories(models.Model):
    intra_pk_id = models.CharField(max_length=100)  # UserProfile의 intra_pk_id와 연결
    request_time = models.DateTimeField(default=timezone.now)  # 요청받은 시간 기록

    def __str__(self):
        # 객체를 문자열로 표현할 때 사용할 방식 정의
        return f"{self.intra_pk_id} - {self.request_time}"
