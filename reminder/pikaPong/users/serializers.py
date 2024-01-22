from rest_framework import serializers
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    # User 모델 관련 필드 추가
    user_id = serializers.CharField(source='user.id', read_only=True)
    # email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user_id', 'intra_pk_id', 'intra_id', 'nick_name', 'profile_picture', 'bio']

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
