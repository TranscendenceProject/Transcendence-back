import json
import secrets
from datetime import datetime, timedelta
from django.db.models import Q

import jwt
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

from .models import UserProfile
from .serializers import CustomTokenObtainPairSerializer
from .serializers import CustomTokenRefreshSerializer
from .serializers import UserProfileSerializer
from friends.models import Friends
from loginHistories.models import LoginHistories
from django.utils import timezone
from datetime import timedelta


class CustomTokenObtainPairView(TokenObtainPairView):
    # Replace the serializer with your custom
    serializer_class = CustomTokenObtainPairSerializer

class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer
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
                'redirect_uri': "http://127.0.0.1:3000"
            },
            headers={'Content-Type': 'application/json'}
        )
        print(token_response)

        if token_response.status_code == 200:
            access_token = token_response.json().get('access_token')

            # User 모델 대신 UserProfile 모델을 사용하여 사용자 데이터 저장
            created, user_profile = save_user_data(access_token)

            otp = generate_otp()
            user_profile.otp_number = otp
            user_profile.save()

            send_email_with_otp(otp, user_profile)

            if created:
                response_data = {'message': 'Created new user profile', 'access_token': access_token}
            else:
                response_data = {'message': 'User profile already exists', 'access_token': access_token}

            return JsonResponse(response_data, status=status.HTTP_200_OK)
        else:
            return JsonResponse({'message': 'Token response is not 200'}, status=status.HTTP_400_BAD_REQUEST)  # Error
    except Exception as e:
        return HttpResponse('Error: ' + str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
def get_JWT_token(request):
    try:
        # 요청 본문에서 JSON 데이터 추출
        data = json.loads(request.body.decode('utf-8')) if request.body else {}

        # JSON 데이터에서 access_token 및 input_number 추출
        access_token = data.get('access_token')
        input_number = data.get('input_number')

        # access_token을 사용하여 UserProfile을 찾음
        user_profile = get_user_profile_by_access_token(access_token)

        print(f"user: {user_profile}")
        print(f"user.otp: {user_profile.otp_number}")

        if user_profile:
            # UserProfile의 otp_number와 입력받은 otp를 비교
            if user_profile.otp_number == input_number:
                # JWT 토큰 및 Refresh 토큰 생성

                jwt_payload = {
                    'intra_pk_id': user_profile.intra_pk_id,  # UserProfile의 실제 ID를 사용
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                jwt_secret_key = settings.SECRET_KEY  # settings.py의 SECRET_KEY 사용
                jwt_token = jwt.encode(jwt_payload, jwt_secret_key, algorithm='HS256').decode('utf-8')

                # JSON 응답 생성 (Access 및 Refresh 토큰 포함)
                response_data = {
                    'status': 'OK',
                    'jwt_token': jwt_token,
                }
                return JsonResponse(response_data, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'status': 'NO'}, status=status.HTTP_400_BAD_REQUEST)  # Error
        else:
            return JsonResponse({'status': 'User profile not found'}, status=status.HTTP_400_BAD_REQUEST)  # Error

    except Exception as e:
        return JsonResponse({'status': 'Error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)  # Error

@csrf_exempt
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
            return UserProfile.objects.get(intra_pk_id=owner_id)
        else:
            return None
    except Exception as e:
        raise e

# 쿼리 파라미터가 있는 경우 -> 다른 사람의 정보를 조회
# 쿼리 파라미터가 없는 경우 -> 내 정보를 조회
@api_view(['GET'])
@csrf_exempt
def get_user_info(request):
    # 쿼리 파라미터에서 intra_pk_id를 가져옴
    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            # JWT 인증
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")
            intra_pk_id = decoded_payload['intra_pk_id']
            try:
                user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)
                # UserProfile 객체가 존재하는 경우의 로직
                target_pk_id = request.query_params.get('target_pk_id')

                if target_pk_id:
                    print(f"다른 사람의 정보를 확인합니다.: {target_pk_id}")
                    try:
                        # target_pk_id를 사용하여 UserProfile 객체를 조회
                        user_profile = UserProfile.objects.get(intra_pk_id=target_pk_id)
                        print("다른 사람의 정보에 도달했습니다.")

                        # UserProfile 객체를 Serializer를 사용하여 직렬화
                        serializer = UserProfileSerializer(user_profile)
                        return Response(serializer.data, status=status.HTTP_200_OK)

                    except UserProfile.DoesNotExist:
                        # intra_pk_id로 UserProfile을 찾을 수 없는 경우
                        return Response({'error': 'target_pk_id에 맞는 UserProfile을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)
                else:
                    print("내 정보를 확인합니다.")
                    try:
                        user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)

                        serializer = UserProfileSerializer(user_profile)
                        return Response(serializer.data)
                    except UserProfile.DoesNotExist:
                        return Response({'error': '유저를 찾을 수 없습니다.'}, status=404)

            except UserProfile.DoesNotExist:
                # UserProfile 객체가 존재하지 않는 경우의 처리
                return Response({'error': 'UserProfile을 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=400)
        except User.DoesNotExist:
            return Response({'user_profiles': []}, status=200)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=400)

@api_view(['POST'])
@csrf_exempt
def set_user_info(request):

    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")
            intra_pk_id = decoded_payload['intra_pk_id']
            user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)

            # Assuming you have a JSON request body with user profile data
            user_profile_data = request.data

            user_profile_serializer = UserProfileSerializer(user_profile, data=user_profile_data, partial=True)
            if user_profile_serializer.is_valid():
                user_profile_serializer.save()  # Save the updated user profile
                return Response(user_profile_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'user_profiles': []}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@csrf_exempt
def search_user_profiles(request):
    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")
            intra_pk_id = decoded_payload['intra_pk_id']
            key_word = request.GET.get('key_word')  # URL query parameter for the search keyword

            if not key_word:
                return Response({'user_profiles': []}, status=status.HTTP_200_OK)
            try:
                # Step 1: Query UserProfile records where intra_id contains the key_word
                user_profiles = UserProfile.objects.filter(Q(intra_id__icontains=key_word))

                user_profiles_list = [
                    {
                        'intra_pk_id': user_profile.intra_pk_id,
                        'intra_id': user_profile.intra_id,
                        'nick_name': user_profile.nick_name,
                        'is_login': False,
                        'is_friend': False
                    } for user_profile in user_profiles if user_profile.intra_pk_id != intra_pk_id
                ]

                user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)
                # 친구 목록 조회
                friends = Friends.objects.filter(user_profile=user_profile)
                friends_list = [{'intra_pk_id': friend.user_profile.intra_pk_id, 'friend_name': friend.friend_name} for
                                friend in friends]

                # 친구 목록에 있는 intra_pk_id를 추출
                friend_names = [friend['friend_name'] for friend in friends_list]

                # user_profiles_list에서 각 항목에 대해 친구 여부 확인 및 업데이트
                for user_profile in user_profiles_list:
                    if user_profile['intra_id'] in friend_names:
                        user_profile['is_friend'] = True

                    latest_login_attempt = LoginHistories.objects.filter(
                        intra_pk_id=user_profile['intra_pk_id']).order_by('-request_time').first()
                    current_time = timezone.now()
                    if latest_login_attempt:
                        # 로그인 시도 시간과 현재 시간의 차이를 계산합니다.
                        time_difference = current_time - latest_login_attempt.request_time

                        # 차이가 5초 이하인 경우, 로그인 상태로 간주합니다.
                        if time_difference.total_seconds() <= 300:
                            user_profile['is_login'] = True

                return JsonResponse({'user_profiles': user_profiles_list}, safe=False, status=200)
            except User.DoesNotExist:
                return Response({'user_profiles': []}, status=status.HTTP_200_OK)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@csrf_exempt
def set_user_info_image(request):

    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")

            file = request.FILES.get('profile_image')
            print(f"file")
            if not file:
                # 파일이 없는 경우, 400 Bad Request 에러 반환
                return Response({"error": "파일이 제공되지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST)

            fs = FileSystemStorage(location=settings.MEDIA_ROOT)  # 파일 시스템 저장소 객체 생성
            filename = fs.save(file.name, file)  # 파일 저장
            file_url = fs.url(filename)  # 저장된 파일의 URL 생성

            # 이후에 필요한 추가 작업 수행
            # 예: UserProfile 모델에 파일 URL 저장

            return Response({'file_url': file_url}, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'user_profiles': []}, status=status.HTTP_404_NOT_FOUND)
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

    if not UserProfile.objects.filter(intra_pk_id=owner_id).exists():

        # 42 API로부터 받은 사용자 정보로부터 필요한 데이터 추출
        owner_data = requests.get(f'https://api.intra.42.fr/v2/users/{owner_id}',
                                  headers={'Authorization': f'Bearer {access_token}'})
        owner_name = owner_data.json().get('login')
        owner_image_link = owner_data.json().get('image', {}).get('link')
        user_profile, created = UserProfile.objects.update_or_create(
            intra_pk_id=owner_id,
            intra_id=owner_name,
            defaults={'profile_picture': owner_image_link}
        )
        return created, user_profile

    else:
        # 이미 존재하는 owner_id의 경우
        print("이미존재하는 계정")
        return False, UserProfile.objects.get(intra_pk_id=owner_id)

def generate_otp(length=6):
    return ''.join([secrets.choice('0123456789') for _ in range(length)])

def send_otp_email(email, otp):
    subject = 'Pikapong login OTP'
    message = f'Your OTP is: {otp}'
    send_mail(subject, message, 'admin@pikapong.com', [email])

    # for test
    # email = 'ejae6467@gmail.com'
    # send_mail(subject, message, 'admin@pikapong.com', [email])