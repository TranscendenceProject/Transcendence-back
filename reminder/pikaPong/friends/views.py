from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import UserProfile, Friends
import jwt
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
@api_view(['POST'])
@csrf_exempt
def add_friend_to_user_profile(request):

    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")
            intra_pk_id = decoded_payload['intra_pk_id']
            friend_intra_pk_id = request.data.get('friend_intra_pk_id')  # 친구의 intra_pk_id

            print(intra_pk_id)
            print(friend_intra_pk_id)

            if not intra_pk_id or not friend_intra_pk_id:
                return JsonResponse({'error': 'Missing intra_pk_id or friend_intra_pk_id'}, status=400)

            if intra_pk_id == friend_intra_pk_id:
                return JsonResponse({'error': '자기 자신은 친구로 등록할 수 없습니다.'}, status=400)

            try:
                user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)
                friend_user_profile = UserProfile.objects.get(intra_pk_id=friend_intra_pk_id)
                print(f"user_profile: {user_profile}")
                print(f"friend_user_profile: {friend_user_profile}")

                # 새로운 Friends 객체 생성 또는 기존 객체 업데이트
                friend, created = Friends.objects.get_or_create(
                    user_profile=user_profile,
                    friend_name=friend_user_profile.intra_id  # friend_name을 식별자로 사용
                )

                # 친구 객체에 friend_user_profile의 정보를 반영 (새로 생성된 경우)
                if created:
                    friend.friend_name = friend_user_profile.intra_id
                    friend.save()

                return JsonResponse({'message': f'{user_profile}가 성공적으로 {friend_user_profile}를 친구로 등록하였습니다.'}, status=200)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'UserProfile not found'}, status=404)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=400)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=400)

@api_view(['GET'])
def get_friends_of_user_profile(request):
    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")
            intra_pk_id = request.GET.get('intra_pk_id')  # URL 쿼리에서 intra_pk_id 추출

            if not intra_pk_id:
                return JsonResponse({'error': 'Missing intra_pk_id'}, status=400)

            try:
                user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)
                friends = Friends.objects.filter(user_profile=user_profile)
                print(friends)

                friends_list = [{'intra_pk_id': friend.user_profile.intra_pk_id, 'friend_name': friend.friend_name} for friend in friends]

                return JsonResponse({'friends': friends_list}, safe=False, status=200)
            except UserProfile.DoesNotExist:
                return JsonResponse({'error': 'UserProfile not found'}, status=404)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'JWT 토큰이 만료되었습니다.'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({'error': 'JWT 토큰을 디코딩하는 데 실패했습니다.'}, status=400)
    else:
        return Response({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=400)


@api_view(['DELETE'])
@csrf_exempt
def remove_friend_from_user_profile(request):
    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            # JWT 토큰 인증
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithms=['HS256'])
            print("JWT 토큰 인증 완료")
            intra_pk_id = decoded_payload['intra_pk_id']
            friend_intra_pk_id = request.data.get('friend_intra_pk_id')  # 삭제할 친구의 intra_pk_id

            if not intra_pk_id or not friend_intra_pk_id:
                return JsonResponse({'error': 'Missing intra_pk_id or friend_intra_pk_id'}, status=400)

            # 자기 자신을 삭제하려는 요청은 거부
            if intra_pk_id == friend_intra_pk_id:
                return JsonResponse({'error': '자기 자신을 친구에서 삭제할 수 없습니다.'}, status=400)

            # 사용자 프로필과 친구 프로필 조회
            user_profile = UserProfile.objects.get(intra_pk_id=intra_pk_id)
            friend_user_profile = UserProfile.objects.get(intra_pk_id=friend_intra_pk_id)

            # 해당 친구 관계를 찾아 삭제
            friend = Friends.objects.get(user_profile=user_profile, friend_name=friend_user_profile.intra_id)
            friend.delete()

            return JsonResponse({'message': f'{user_profile}가 성공적으로 {friend_user_profile}를 친구 목록에서 삭제하였습니다.'}, status=200)
        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'UserProfile not found'}, status=404)
        except Friends.DoesNotExist:
            return JsonResponse({'error': '해당 친구 관계가 존재하지 않습니다.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'JWT 토큰이 요청에 포함되어야 합니다.'}, status=400)