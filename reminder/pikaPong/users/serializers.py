from datetime import datetime, timedelta

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.state import token_backend

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ['intra_pk_id', 'intra_id', 'nick_name', 'profile_picture', 'bio', 'histories']

    def update(self, instance, validated_data):
        # nick_name 필드 업데이트
        if 'nick_name' in validated_data:
            instance.nick_name = validated_data['nick_name']

        # profile_picture 필드 업데이트
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']

        # bio 필드 업데이트
        if 'bio' in validated_data:
            instance.bio = validated_data['bio']

        instance.save()  # 변경된 필드 저장
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # 기본 토큰 결과 (access/refresh tokens)
        data = super(CustomTokenObtainPairSerializer, self).validate(attrs)

        # self.user는 현재 인증된 사용자 객체를 나타냄
        # UserProfile 객체 조회
        user_profile = UserProfile.objects.get(intra_pk_id=self.user.intra_pk_id)

        # 사용자 지정 데이터 포함
        data.update({'intra_pk_id': user_profile.intra_pk_id})
        data.update({'exp': datetime.utcnow() + timedelta(hours=1)})

        return data

class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        data = super(CustomTokenRefreshSerializer, self).validate(attrs)
        decoded_payload = token_backend.decode(data['access'], verify=True)
        user_uid = decoded_payload['intra_pk_id']

        print(user_uid)
        # add filter query
        data.update({'intra_pk_id': user_uid})
        data.update({'exp': datetime.utcnow() + timedelta(hours=1)})
        return data