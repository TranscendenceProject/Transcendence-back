from rest_framework.decorators import api_view

from .models import UserProfile, Friend


# Create your views here.
@api_view(['POST'])
def add_friend_to_user_profile(request):
    intra_pk_id = request.data.get('intra_pk_id')
    friends_pk_id = request.data.get('friends_pk_id')

    print(f"intra: {intra_pk_id}")
    print(f"friends: {friends_pk_id}")

    if not intra_pk_id or not friends_pk_id:
        return JsonResponse({'error': 'Missing intra_pk_id or friends_pk_id'}, status=400)

    try:
        user_profile = UserProfile.objects.get(pk=intra_pk_id)
        friend = Friend.objects.get(pk=friends_pk_id)
        friend.user_profile = user_profile
        friend.save()
        return JsonResponse({'message': 'Friend added successfully to UserProfile'}, status=200)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'UserProfile not found'}, status=404)
    except Friend.DoesNotExist:
        return JsonResponse({'error': 'Friend not found'}, status=404)
    except Exception as e:
        # 예외가 입력 오류로 인한 것이 아닐 경우 500으로 처리
        return JsonResponse({'error': str(e)}, status=500)
