# login

## 실행

_/Transcendence-back/reminder_ 

- venv 가상환경 활성화
    ```
        source venv/bin/activate
    ```
  
- venv 가상환경 비활성화
    ```
        deactivate 
    ```

_/Transcendence-back/reminder/remindeProject_

- 서버 실행
    ```
        python manage.py runserver
    ```
  
- 서버 종료
    ```
        CONTROL-C.
    ```

----

## 메서드 설명

### get_resource_owner_42_id

1. 매개변수

    - 프론트에서 42login 을 통해 얻은 code 값을 받음

2. 로직

    - code 값을 통해 42서버에 유효성 검증을 하고 token_response을 얻음
    - token_response 으로 42pk(access_token) 값을 얻을 수 있으며 이를 통해 user의 DB 값을 받아옴
    - DB 값으로는 다음과 같음
      - external_id(PK)
      - external_name(email 전송을 위해 인트라 아이디 저장)
      - profile_picture(url 경로)
      - otp_number(생성된 otp 숫자 6자리, 유효 시간은 미구현)
      - 해당 이메일로 otp 번호 발송
   - DB 저장 후에 프론트에 응답
     - 새로 생성된 경우, 이미 생성된 경우에따라 메세지가 다름
       - response_data = {'message': 'Created new user profile', 'access_token': access_token}
       - response_data = {'message': 'User profile already exists', 'access_token': access_token}
     - 잘못된 code 의 경우 
       - return JsonResponse({'message': 'token_response is not 200'})
     - 에러 발생의 경우
       - return HttpResponse('Error: ' + str(e))
     

### get_JWT_token

1. 매개변수

    - json body 부에 입력한 값을 받아옴
   ```
    {
        "access_token": "d85fed811370d06424c73c8103c4c6629c10da4793b74227a9e1a701610cac11",
        "input_number": "130577"
    }
   ``` 

2. 로직

    - 사용자의 otp 번호와 입력 otp 값을 비교한 후 맞으면 JWT 토큰 반환
      - return JsonResponse(response_data)
    - 틀리면 
      - return JsonResponse({'status': 'NO'})
    - 유저가 없다면 
      - return JsonResponse({'status': 'User not found'})
    - 에러 발생의 경우
      - return JsonResponse({'status': 'Error', 'message': str(e)})
