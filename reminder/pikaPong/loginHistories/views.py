from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import LoginHistories
from django.utils import timezone
import jwt
from django.conf import settings


@require_http_methods(["POST"])
@csrf_exempt
def save_login_info(request):
    jwt_token = request.META.get("HTTP_JWT")

    if jwt_token:
        try:
            # JWT 인증
            decoded_payload = jwt.decode(jwt_token, settings.SECRET_KEY, algorithm='HS256')
            print("JWT 토큰 인증 완료")
            intra_pk_id = decoded_payload['intra_pk_id']

            if not intra_pk_id:
                return JsonResponse({'error': 'Missing intra_pk_id'}, status=400)

            # 새로운 LoginHistories 인스턴스를 생성하고 저장합니다.
            login_history = LoginHistories.objects.create(
                intra_pk_id=intra_pk_id,
                request_time=timezone.now()  # 현재 시간을 기록합니다.
            )
            login_history.save()

            # 성공 응답을 반환합니다.
            return JsonResponse({'message': 'Login 정보를 성공적으로 저장했습니다'}, status=201)

        except Exception as e:
            # 예외가 발생하면 에러 응답을 반환합니다.
            return JsonResponse({'error': str(e)}, status=500)

