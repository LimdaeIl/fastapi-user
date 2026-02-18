# fastapi-user
### 최초 아키텍처 설계 내역
```pgsql
fastapi-user/
  app/
    main.py
    core/
      config.py
      logging.py
      security/
        password.py
        jwt.py
      exceptions.py
      deps.py
    db/
      session.py
      base.py
      migrations/            # alembic
    infra/
      redis.py
    modules/
      auth/
        router.py
        schemas.py
        service.py
      users/
        router.py
        schemas.py
        service.py
        repository.py
        models.py
      devices/
        router.py
        schemas.py
        service.py
        repository.py
        models.py
    common/
      enums.py
      utils.py
      pagination.py
  tests/
    unit/
    integration/
```


- API 계층 (router): HTTP/요청·응답, 의존성 주입, validation
- Service 계층: 비즈니스 로직(회원가입/로그인/세션정책)
- Repository 계층: DB 접근(SQLAlchemy)
- Domain/Model 계층: SQLAlchemy 모델 + 도메인 타입(Enum)
- Schemas 계층: Pydantic DTO (Request/Response)
- Infra 계층: MySQL 세션, Redis, 보안(패스워드 해시/JWT), 설정, 로깅

### modules
도메인 단위로 분리하고, 각 모듈은 보통 아래 5개 파일 패턴을 유지하는 것을 권장
1. router.py : 엔드포인트
2. schemas.py : Pydantic DTO
3. service.py : 로직
4. repository.py : DB access
5. models.py : SQLAlchemy 모델

### 의존성 선택
- ORM: SQLAlchemy 2.0 + Alembic
- 설정: pydantic-settings
- 인증: JWT (pyjwt 또는 python-jose)
- 비밀번호 해시: passlib[bcrypt]
- Redis: redis-py
- 테스트: pytest + httpx + testcontainers(선택)

### 회원, 디바이스, 세션(Redis)에 맞춘 모듈 경계를 구분
**auth 모듈**
- 로그인, 토큰 재발급, 로그아웃
- Redis 세션 관리(sessionId, refresh hash, single-device 정책 적용)

**users 모듈**
- 회원가입/조회/수정/탈퇴(soft delete)
- 이메일/전화 인증 상태, 프로필 이미지

**devices 모듈**
- 로그인 시 device upsert/등록, 마지막 접속 기록
- (나중에) 기기 차단, 신뢰 디바이스 

모듈 설계 포인트: 세션은 auth, 기기 정보는 devices, 사용자 정보는 users로 경계를 잡으면 확장할 때 자연스러울 것으로 판단했습니다.

### 설계 규칙
1. DTO는 XxxRequest, XxxResponse로 통일
2. 라우터 prefix는 버전 포함: /v1/auth, /v1/users, /v1/devices
3. 모든 엔드포인트는 service만 호출(라우터에 로직 금지)
4. DB 접근은 repository로만(서비스에서 쿼리 직접 작성 금지)
5. 에러는 core/exceptions.py에 표준화 (예: AuthError, NotFoundError)



