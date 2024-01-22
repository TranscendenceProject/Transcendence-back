from django.shortcuts import render, HttpResponse
from .models import UserProfile
import requests
import secrets
from django.contrib.auth.models import User
from django.core.mail import send_mail
import jwt
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
import json
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserProfileSerializer

# Create your views here.
# def index(request):
#     return HttpResponse('index!')

def get_resource_owner_42_id(request, code):
    try:
        # 토큰 받기 위한 요청
        token_response = requests.post(
            'https://api.intra.42.fr/oauth/token',
            json={
                'grant_type': 'authorization_code',
                'client_id': 'u-s4t2ud-b677e803809d207e81ae3a321bdf542af8d318ca330d81824e4b972bca224918',
                'client_secret': "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",
                'code': code,
                'redirect_uri': "http://127.0.0.1"
            },
            headers={'Content-Type': 'application/json'}
        )
        print(token_response)

        if token_response.status_code == 200:
            access_token = token_response.json().get('access_token')

            print(access_token)

            created, user = save_user_data(access_token)

            response_data = {
                'message': 'New user profile created' if created else 'User profile already exists',
                'access_token': access_token
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'message': 'Token response is not 200'})  # Error
    except Exception as e:
        return HttpResponse('Error: ' + str(e))


@csrf_exempt
def get_JWT_token(request):
    try:
        # 요청 본문에서 JSON 데이터 추출
        data = json.loads(request.body.decode('utf-8')) if request.body else {}

        # JSON 데이터에서 access_token 및 input_number 추출
        access_token = data.get('access_token')
        input_number = data.get('input_number')

        # access_token을 사용하여 사용자를 찾음
        user = get_user_profile_by_access_token(access_token)

        print(f"user: {user}")
        print(f"user.otp: {user.userprofile.otp_number}")

        if user:
            # 사용자의 otp_number와 입력받은 otp를 비교
            if user.userprofile.otp_number == input_number:
                # OTP 일치 시 JWT 토큰 생성
                # JWT 토큰 생성 시 User 모델의 ID 사용
                print(f"user.id: {user.id}")
                jwt_payload = {
                    'user_id': user.id,  # user 모델의 실제 ID를 사용해야 함
                    'exp': datetime.utcnow() + timedelta(hours=1)
                }
                jwt_secret_key = settings.SECRET_KEY  # settings.py의 SECRET_KEY 사용
                jwt_token = jwt.encode(jwt_payload, jwt_secret_key, algorithm='HS256').decode('utf-8')
                # JSON 응답 생성
                response_data = {
                    'status': 'OK',
                    'jwt_token': jwt_token
                }
                return JsonResponse(response_data)
            else:
                return JsonResponse({'status': 'NO'})
        else:
            return JsonResponse({'status': 'User not found'})

    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)})


def get_user_profile_by_access_token(access_token):
    try:
        # access_token을 사용하여 사용자를 찾음
        owner_response = requests.get(
            'https://api.intra.42.fr/oauth/token/info',
            headers={'Authorization': f'Bearer {access_token}'}
        )

        owner_id = owner_response.json().get('resource_owner_id')

        # User 모델과 UserProfile 모델 연결 사용
        if UserProfile.objects.filter(intra_pk_id=owner_id).exists():
            return UserProfile.objects.get(intra_pk_id=owner_id).user
        else:
            return None
    except Exception as e:
        raise e

@api_view(['GET'])
def get_user_info(request, jwt_token):

    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            user_id = decoded_payload['user_id']
            user = User.objects.get(id=user_id)
            user_profile = user.userprofile
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data)
        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=400)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=400)
        except User.DoesNotExist:
            return Response({'error': '유저를 찾을 수 없습니다.'}, status=404)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=400)



@api_view(['POST'])
def set_user_info(request, jwt_token):
    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            user_id = decoded_payload['user_id']
            user = User.objects.get(id=user_id)

            # Assuming you have a JSON request body with user profile data
            user_profile_data = request.data
            user_profile_instance = user.userprofile

            # Update user profile fields using the modified serializer
            user_profile_serializer = UserProfileSerializer(user_profile_instance, data=user_profile_data, partial=True)
            print("test")
            if user_profile_serializer.is_valid():
                user_profile_serializer.save()  # Save the updated user profile
                return Response(user_profile_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': '유저를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

def send_email_with_otp(otp, user_profile):
    # otp 토큰 발급
    print(f'이메일로 보낼 otp: {otp}')

    # intra_id이 None이 아닐 경우에만 이메일 주소 생성
    if user_profile.intra_id:
        user_email = user_profile.intra_id + "@student.42seoul.kr"
        print(f'이메일 : {user_email}')
        send_otp_email(user_email, otp)  # 이메일을 UserProfile 모델에 저장했다고 가정
        print('이메일을 발송하였습니다.')
    else:
        print("이메일 주소가 없습니다.")

def save_user_data(access_token):
    owner_response = requests.get(
        'https://api.intra.42.fr/oauth/token/info',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    owner_id = owner_response.json().get('resource_owner_id')

    print(f'owner_id: {owner_id}')

    # 42 API로부터 받은 사용자 정보로부터 필요한 데이터 추출
    owner_data = requests.get(f'https://api.intra.42.fr/v2/users/{owner_id}',
                              headers={'Authorization': f'Bearer {access_token}'})
    owner_name = owner_data.json().get('login')
    owner_image_link = owner_data.json().get('image', {}).get('link')

    # User 모델과 UserProfile 모델을 함께 업데이트
    user, created = User.objects.get_or_create(username=owner_name)
    user_profile, _ = UserProfile.objects.update_or_create(
        user=user,
        defaults={
            'intra_pk_id': owner_id,
            'intra_id': owner_name,
            'profile_picture': owner_image_link,
            # 기타 필요한 필드
        }
    )

    # OTP 번호 업데이트
    otp = generate_otp()
    user_profile.otp_number = otp
    user_profile.save()

    # 이메일 전송 로직 (생략 가능)
    send_email_with_otp(otp, user_profile)

    return user, created


def generate_otp(length=6):
    return ''.join([secrets.choice('0123456789') for _ in range(length)])

def send_otp_email(email, otp):
    subject = 'Pikapong login OTP'
    message = f'Your OTP is: {otp}'
    send_mail(subject, message, 'admin@pikapong.com', [email])

    # for test
    # email = 'ejae6467@gmail.com'
    # send_mail(subject, message, 'admin@pikapong.com', [email])