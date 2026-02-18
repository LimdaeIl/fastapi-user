아래는 **지금까지 구현한 내용(쿠키 기반 JWT + Refresh Rotation + Redis 세션 바인딩 + 즉시 revoke + replay 방지 + `/auth/refresh` + 로그아웃 세션 제거)**을 기준으로, 바로 `README.md`에 붙여 넣을 수 있는 **상세 문서 템플릿**이야.
(프로젝트명/포트/엔드포인트는 네 코드에 맞춰 `http://127.0.0.1:8000/api/v1` 기준으로 작성했어.)

---

````md
# fastapi-user 인증 시스템 (Cookie 기반 JWT + Refresh Rotation)

이 프로젝트는 FastAPI에서 **Access/Refresh 토큰을 Response Body로 전달하지 않고**,  
**HttpOnly Cookie**로만 전달하는 방식의 인증 시스템을 구현합니다.

또한 Refresh Token에 대해 **Rotation(회전) + Redis 기반 세션 바인딩**을 적용해 다음을 보장합니다.

- Refresh Token 재발급 시 **기존 Refresh Token 즉시 무효화**
- 이전 Refresh Token 재사용(replay) 시도 시 **세션 폐기**
- Logout 시 Redis 세션 삭제로 **즉시 인증 무효화(Access 포함)**

---

## 목차

- [요구사항과 목표](#요구사항과-목표)
- [핵심 설계](#핵심-설계)
  - [토큰 전달 방식](#토큰-전달-방식)
  - [JWT Payload](#jwt-payload)
  - [Redis 세션 저장 구조](#redis-세션-저장-구조)
  - [Refresh Rotation](#refresh-rotation)
  - [Logout / 즉시 revoke](#logout--즉시-revoke)
  - [Access 즉시 무효화](#access-즉시-무효화)
- [엔드포인트](#엔드포인트)
- [설정](#설정)
  - [.env 예시](#env-예시)
  - [CORS / 쿠키](#cors--쿠키)
- [동작 시나리오](#동작-시나리오)
- [테스트](#테스트)
  - [PyCharm .http 테스트 예시](#pycharm-http-테스트-예시)
  - [Redis 확인](#redis-확인)
- [보안 고려사항](#보안-고려사항)
- [트러블슈팅](#트러블슈팅)

---

## 요구사항과 목표

### 목표
- 로그인 성공 시 토큰을 **Response Body로 전달하지 않고**
- **HttpOnly Cookie**로만 전달하여 프론트엔드 JS에서 토큰에 접근하지 못하도록 함 (XSS 완화)
- Refresh Token은 Redis에 세션 상태를 저장하여 **Rotation + Replay 방지**
- Logout 시 세션 삭제로 **즉시 revoke** 가능하도록 설계

---

## 핵심 설계

### 토큰 전달 방식

- Access Token: `HttpOnly Cookie`
- Refresh Token: `HttpOnly Cookie`
- 응답 바디에는 토큰을 포함하지 않으며, `{ "ok": true }` 등 최소 응답만 반환

쿠키 이름은 설정으로 관리합니다.

- `COOKIE_ACCESS_NAME = "access_token"`
- `COOKIE_REFRESH_NAME = "refresh_token"`

---

### JWT Payload

#### Access Token payload
- `sub`: 사용자 ID (문자열)
- `sid`: 세션 ID (uuid4 hex)
- `typ`: `"access"`
- `iat`: 발급 시각 epoch seconds
- `exp`: 만료 시각 epoch seconds

예시:
```json
{
  "sub": "1",
  "sid": "9f4a1b8e2c0d4f6ab91d6e1a72b4c321",
  "typ": "access",
  "iat": 1700000000,
  "exp": 1700000900
}
````

#### Refresh Token payload

* `sub`: 사용자 ID
* `sid`: 세션 ID (Access와 동일)
* `jti`: refresh token 고유 ID (uuid4 hex)
* `typ`: `"refresh"`
* `iat`, `exp`

예시:

```json
{
  "sub": "1",
  "sid": "9f4a1b8e2c0d4f6ab91d6e1a72b4c321",
  "jti": "c82e9d0f0e9e4bb9a7e9f0a6c51e2f11",
  "typ": "refresh",
  "iat": 1700000000,
  "exp": 1701200000
}
```

---

### Redis 세션 저장 구조

Refresh Token Rotation을 위해 Redis에 세션 상태를 저장합니다.

#### Redis Key

```
sess:{user_id}:{sid}
```

* `user_id`: JWT `sub`
* `sid`: 로그인 세션 ID (`create_session_id()`로 생성)

예시:

```
sess:1:9f4a1b8e2c0d4f6ab91d6e1a72b4c321
```

#### Redis Value

```
current_refresh_jti
```

* Refresh Token payload의 `jti` 값만 저장
* JWT 전체를 저장하지 않음

예시:

```
KEY:   sess:1:9f4a1...
VALUE: "c82e9d0f0e9e..."
```

#### TTL

Redis Key TTL은 Refresh 만료 시간과 동일하게 설정합니다.

* `REFRESH_TOKEN_EXPIRE_SECONDS`

---

### Refresh Rotation

`POST /auth/refresh` 호출 시:

1. 쿠키에서 refresh token 조회
2. refresh JWT decode 및 typ 검증
3. Redis에서 `sess:{user_id}:{sid}` 조회 → `current_jti` 획득
4. `current_jti`와 refresh token의 `jti`를 비교

   * 일치 → 정상
   * 불일치 → replay(재사용) 또는 탈취 의심
5. 정상인 경우:

   * 새 access token 발급
   * 새 refresh token 발급(새 `jti`)
   * Redis의 `sess:{user_id}:{sid}` 값을 새 `jti`로 덮어쓰기 (기존 refresh 즉시 무효)
   * 새 쿠키를 response에 set

#### replay 탐지 및 대응

* `current_jti != presented_jti`인 경우

  * `delete_session(user_id, sid)`로 세션 폐기
  * 쿠키 제거
  * 401 반환

---

### Logout / 즉시 revoke

`POST /auth/logout` 호출 시:

1. 쿠키에서 refresh token 조회
2. refresh token decode 후 `sub`, `sid` 추출
3. Redis에서 `sess:{user_id}:{sid}` 삭제 (세션 revoke)
4. access/refresh 쿠키를 `Max-Age=0`로 삭제

---

### Access 즉시 무효화

기본 JWT는 stateless이므로 access token은 원래 “만료 전까지” 유효합니다.

하지만 이 프로젝트는 **세션 바인딩**을 통해 access token도 즉시 revoke가 가능합니다.

`get_current_user`에서:

* access JWT decode
* `sub`, `sid` 추출
* Redis에서 `sess:{sub}:{sid}` 존재 여부 확인

  * 존재하지 않으면(로그아웃/세션만료/침해로 세션 삭제) → 401

즉, **Redis 세션이 삭제되는 순간 access token도 즉시 무효화**됩니다.

---

## 엔드포인트

Base URL:

* `http://127.0.0.1:8000/api/v1`

### Auth

* `POST /auth/signup`

  * body: email, nickname, password
  * 성공: 사용자 생성

* `POST /auth/login`

  * body: email, password
  * 성공:

    * `Set-Cookie: access_token=...; HttpOnly`
    * `Set-Cookie: refresh_token=...; HttpOnly`
    * Redis에 세션 저장

* `POST /auth/refresh`

  * 쿠키의 refresh token 기반
  * 성공:

    * 새 access/refresh 쿠키 재발급
    * Redis의 refresh `jti` 갱신 (rotation)

* `POST /auth/logout`

  * 쿠키의 refresh token 기반
  * 성공:

    * Redis 세션 삭제
    * access/refresh 쿠키 삭제

### Users (예: 인증 필요 엔드포인트)

* `GET /users/me`

  * `get_current_user` dependency로 access cookie 인증
  * Redis 세션 바인딩 확인

---

## 설정

### .env 예시

```env
APP_ENV=local
DEBUG=true
CORS_ORIGINS=http://localhost:5173

DB_HOST=localhost
DB_PORT=3307
DB_NAME=fastapi_user
DB_USER=root
DB_PASSWORD=root

REDIS_URL=redis://localhost:6379/0

JWT_SECRET=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_SECONDS=900
REFRESH_TOKEN_EXPIRE_SECONDS=1209600

COOKIE_SECURE=false
COOKIE_SAMESITE=lax
```

> 로컬 개발(HTTP)에서는 `COOKIE_SECURE=false` 권장
> HTTPS 환경에서는 `COOKIE_SECURE=true` 및 필요 시 `COOKIE_SAMESITE=none` 사용

---

### CORS / 쿠키

쿠키 기반 인증을 위해 CORS 설정에서:

* `allow_credentials=True`
* `allow_origins`는 `*` 대신 명시 origin 사용 권장

프론트엔드에서는 요청 시:

* fetch: `credentials: "include"`
* axios: `withCredentials: true`

---

## 동작 시나리오

### 로그인

1. `/auth/login` 호출
2. access/refresh 쿠키 발급
3. Redis에 `sess:{user_id}:{sid} -> refresh_jti` 저장

### API 호출

1. `/users/me` 호출
2. `get_current_user`가 access cookie를 decode
3. Redis 세션 존재 확인
4. user 조회 후 반환

### 토큰 재발급(Refresh)

1. `/auth/refresh` 호출
2. refresh cookie decode
3. Redis에 저장된 `jti`와 비교
4. 새 access/refresh 쿠키 발급 + Redis `jti` 업데이트

### 로그아웃

1. `/auth/logout` 호출
2. Redis 세션 삭제
3. 쿠키 삭제
4. 이후 access token도 Redis 세션이 없으므로 즉시 차단됨

---

## 테스트

### PyCharm .http 테스트 예시

```http
// POST

### 회원가입
POST http://127.0.0.1:8000/api/v1/auth/signup
Content-Type: application/json
Accept: application/json

{
  "email": "test2@example.com",
  "nickname": "testuser2",
  "password": "Password123!"
}

### 로그인
POST http://127.0.0.1:8000/api/v1/auth/login
Content-Type: application/json
Accept: application/json

{
  "email": "test2@example.com",
  "password": "Password123!"
}

### 보호 API
GET http://127.0.0.1:8000/api/v1/users/me
Accept: application/json

### refresh
POST http://127.0.0.1:8000/api/v1/auth/refresh
Accept: application/json

### 로그아웃
POST http://127.0.0.1:8000/api/v1/auth/logout
Accept: application/json

### 로그아웃 후 보호 API (401 기대)
GET http://127.0.0.1:8000/api/v1/users/me
Accept: application/json
```

---

### Redis 확인

로그인 직후:

```bash
redis-cli
KEYS sess:*
```

Refresh 후(값 변경 확인):

```bash
GET sess:{user_id}:{sid}
```

Logout 후:

```bash
KEYS sess:*
```

---

## 보안 고려사항

* Access/Refresh는 HttpOnly 쿠키로만 전달 → JS 접근 차단(XSS 완화)
* Refresh Rotation 적용 → 이전 refresh 재사용(replay) 방지
* replay 탐지 시 세션 폐기 + 쿠키 삭제
* Redis 세션 바인딩으로 access도 즉시 revoke 가능
* Access TTL은 짧게(예: 15분) 유지 권장

---

## 트러블슈팅

### 로컬에서 쿠키가 저장되지 않음

* `COOKIE_SECURE=true`이면 HTTP 환경에서 쿠키 저장이 안 될 수 있음
* 로컬은 `COOKIE_SECURE=false`로 설정

### CORS 에러 / 쿠키 미전송

* `allow_credentials=True` 확인
* 프론트 요청에 `credentials: "include"` 확인
* `allow_origins="*"` 사용 중이면 credentials와 함께 동작하지 않음

### refresh가 항상 401

* Redis에 `sess:{user_id}:{sid}`가 존재하는지 확인
* refresh token의 `jti`가 Redis 값과 일치하는지 확인
* logout 또는 TTL 만료로 세션이 삭제된 상태인지 확인

```

---

원하면 내가 **네 현재 프로젝트 파일 구조**에 맞춰 README를 더 “프로덕션 문서”처럼 다듬어줄 수도 있어. 예를 들면:

- 폴더 구조/모듈별 책임(routers/services/security/infra)
- 에러 응답 포맷(AppException, domain_code, type, instance)
- 쿠키 옵션(SameSite/Domain/Secure) 케이스별 표
- rotation/replay 흐름 시퀀스 다이어그램(텍스트 기반)

원하는 README 톤이 **팀 문서(설계/근거 중심)**인지, **사용자 가이드(실행/테스트 중심)**인지 말해주면 그 스타일로 재작성해줄게.
::contentReference[oaicite:0]{index=0}
```
