from django.shortcuts import render, HttpResponse
from .models import UserProfile
import requests
import secrets
from django.core.mail import send_mail
import jwt
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt

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

        if token_response.status_code == 200:

            access_token = token_response.json().get('access_token')

            print(access_token)

            created, user_profile = save_user_data(access_token)

            otp = generate_otp()
            user_profile.otp_number = otp
            user_profile.save()

            send_email_with_otp(otp, user_profile)

            if created:
                response_data = {'message': 'Created new user profile', 'access_token': access_token}
            else:
                response_data = {'message': 'User profile already exists', 'access_token': access_token}

            return JsonResponse(response_data)
        else:
            return JsonResponse({'message': 'token_response is not 200'})
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
        user_profile = get_user_profile_by_access_token(access_token)

        if user_profile:
            # 사용자의 otp_number와 입력받은 otp를 비교
            if user_profile.otp_number == input_number:
                # OTP 일치 시 JWT 토큰 생성
                jwt_payload = {
                    'user_id': user_profile.external_id,
                    'exp': datetime.utcnow() + timedelta(hours=1)  # 토큰 만료 시간 설정 (예: 1시간)
                }
                jwt_secret_key = settings.SECRET_KEY  # settings.py의 SECRET_KEY 사용
                jwt_token = jwt.encode(jwt_payload, jwt_secret_key, algorithm='HS256')
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

        if UserProfile.objects.filter(external_id=owner_id).exists():
            return UserProfile.objects.get(external_id=owner_id)
        else:
            return None

    except Exception as e:
        raise e

def send_email_with_otp(otp, user_profile):
    # otp 토큰 발급
    print(f'이메일로 보낼 otp: {otp}')
    user_email = user_profile.external_name + "@student.42seoul.kr"
    print(f'이메일 : {user_email}')
    send_otp_email(user_email, otp)  # 이메일을 UserProfile 모델에 저장했다고 가정
    print('이메일을 발송하였습니다.')

def save_user_data(access_token):
    # 토큰 정보를 사용하여 리소스 소유자 정보 가져오기
    owner_response = requests.get(
        'https://api.intra.42.fr/oauth/token/info',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    # 소유자 고유 번호 정보 가져오기
    # print(owner_response.json().get('resource_owner_id'))
    owner_id = owner_response.json().get('resource_owner_id')
    if not UserProfile.objects.filter(external_id=owner_id).exists():

        # 소유자 고유 정보를 통해 원하는 정보 42 사이트에서 가져오기
        owner_data = requests.get(f'https://api.intra.42.fr/v2/users/{owner_id}',
                                  headers={'Authorization': f'Bearer {access_token}'}
                                  )
        owner_name = owner_data.json().get('login')
        # 소유자 'image' 데이터에서 'link' 값 추출
        owner_image_link = owner_data.json().get('image', {}).get('link')
        print('Image Link:', owner_image_link)
            # 프로필 사진 URL도 받아와야 한다면 여기에 추가
        user_profile, created = UserProfile.objects.update_or_create(
            external_id=owner_id,
            external_name=owner_name,
            defaults={'profile_picture': owner_image_link}
        )
        return created, user_profile
    else:
        # 이미 존재하는 owner_id의 경우
        return False, UserProfile.objects.get(external_id=owner_id)

def generate_otp(length=6):
    return ''.join([secrets.choice('0123456789') for _ in range(length)])

def send_otp_email(email, otp):
    subject = 'Pikapong login OTP'
    message = f'Your OTP is: {otp}'
    send_mail(subject, message, 'admin@pikapong.com', [email])

    # for test
    # email = 'ejae6467@gmail.com'
    # send_mail(subject, message, 'admin@pikapong.com', [email])