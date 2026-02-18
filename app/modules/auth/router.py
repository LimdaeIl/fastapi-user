# app/modules/auth/router.py
from __future__ import annotations

from fastapi import APIRouter, Response, Depends
from fastapi import Request

from app.common.responses.success import ok
from app.modules.auth.schemas import SignUpRequest, LoginRequest, LoginResponse
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup")
def sign_up(req: SignUpRequest, svc: AuthService = Depends()):
  user = svc.signup(
      email=req.email,
      nickname=req.nickname,
      password=req.password,
  )
  return ok(UserResponse.from_model(user).model_dump())


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, response: Response, svc: AuthService = Depends()):
  svc.login_and_set_cookies(response, email=req.email, password=req.password)
  return LoginResponse(ok=True)


@router.post("/refresh")
def refresh(request: Request, response: Response, svc: AuthService = Depends()):
  svc.refresh(request, response)
  return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response, svc: AuthService = Depends()):
  svc.logout(request, response)
  return {"ok": True}
