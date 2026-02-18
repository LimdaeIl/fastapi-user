from __future__ import annotations


def test_signup_success(client):
    res = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "nickname": "테스터",
            "password": "password1234",
        },
    )
    assert res.status_code == 200

    body = res.json()
    assert body["status"] == 200
    assert body["success"] is True
    assert "data" in body

    data = body["data"]
    assert data["email"] == "test@example.com"
    assert data["nickname"] == "테스터"
    assert data["role"] == "USER"
    assert data["id"] > 0


def test_signup_validation_error(client):
    # email 형식 오류 + nickname 길이 + password 길이
    res = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "not-email",
            "nickname": "a",
            "password": "123",
        },
    )
    assert res.status_code == 422

    body = res.json()
    # RFC7807 최상위 응답
    assert body["status"] == 422
    assert body["title"] == "Validation Error"
    assert body["detail"] == "Request validation failed"
    assert body["code"] == "VALIDATION_ERROR"
    assert "errors" in body


def test_signup_email_conflict(client):
  payload = {
    "email": "test@test.com",
    "nickname": "tester",
    "password": "password1234",
  }

  # 첫 가입 성공        "/api/v1/auth/signup",
  res1 = client.post("/api/v1/auth/signup", json=payload)
  assert res1.status_code == 200

  # 두 번째 가입 → 충돌
  res2 = client.post("/api/v1/auth/signup", json=payload)

  assert res2.status_code == 409
  body = res2.json()

  assert body["code"] == "CONFLICT"
  assert body["detail"] == "회원: 이미 사용 중인 이메일입니다."
