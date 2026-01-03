from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.email_verification import VerificationType
from app.services.auth import (
    hash_password, verify_password, create_access_token,
    get_user_by_email, create_verification_code, verify_code,
    check_rate_limit, increment_rate_limit, reset_rate_limit,
    lock_user_account, check_and_unlock_user
)
from app.services.email_webhook import send_verification_email
from app.api.dependencies import get_current_user


router = APIRouter()


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRegisterRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyLoginRequest(BaseModel):
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str
    remaining_attempts: int | None = None


def get_client_ip(request: Request) -> str:
    """İstemci IP adresini al"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=MessageResponse)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Yeni kullanıcı kaydı - email doğrulama kodu gönderir"""
    client_ip = get_client_ip(request)
    email = data.email.lower()
    
    # Rate limit kontrolü - IP bazlı
    allowed, remaining = await check_rate_limit(
        db, client_ip, "register_attempt",
        max_attempts=5, window_minutes=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla kayıt denemesi. Lütfen 1 saat sonra tekrar deneyin."
        )
    
    # Email zaten kayıtlı mı?
    existing_user = await get_user_by_email(db, email)
    if existing_user:
        if existing_user.is_verified:
            await increment_rate_limit(db, client_ip, "register_attempt", 60)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email adresi zaten kayıtlı"
            )
        else:
            # Doğrulanmamış hesap varsa, yeni kod gönder
            pass
    
    # Email gönderim rate limit kontrolü
    allowed, _ = await check_rate_limit(
        db, email, "email_send",
        max_attempts=settings.email_max_sends,
        window_minutes=settings.email_window_minutes
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Bu email adresine çok fazla kod gönderildi. {settings.email_window_minutes} dakika sonra tekrar deneyin."
        )
    
    # Şifre uzunluğu kontrolü
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Şifre en az 8 karakter olmalıdır"
        )
    
    # Kullanıcı yoksa oluştur
    if not existing_user:
        user = User(
            email=email,
            password_hash=hash_password(data.password),
            is_verified=False
        )
        db.add(user)
        await db.commit()
    else:
        # Varolan ama doğrulanmamış kullanıcının şifresini güncelle
        existing_user.password_hash = hash_password(data.password)
        await db.commit()
    
    # Doğrulama kodu oluştur ve gönder
    code = await create_verification_code(db, email, VerificationType.REGISTER)
    await increment_rate_limit(db, email, "email_send", settings.email_window_minutes)
    
    email_sent = await send_verification_email(email, code)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email gönderilemedi. Lütfen tekrar deneyin."
        )
    
    return MessageResponse(
        message="Doğrulama kodu email adresinize gönderildi",
        remaining_attempts=remaining
    )


@router.post("/verify-register", response_model=TokenResponse)
async def verify_register(
    data: VerifyRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Kayıt doğrulama kodunu kontrol et ve token döndür"""
    email = data.email.lower()
    
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kullanıcı bulunamadı"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu hesap zaten doğrulanmış"
        )
    
    is_valid = await verify_code(db, email, data.code, VerificationType.REGISTER)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama kodu"
        )
    
    # Kullanıcıyı doğrulanmış olarak işaretle
    user.is_verified = True
    await db.commit()
    
    # Token oluştur ve döndür
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=MessageResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Giriş - şifre kontrolü yapıp doğrulama kodu gönderir"""
    client_ip = get_client_ip(request)
    email = data.email.lower()
    
    # IP bazlı rate limit
    allowed, remaining = await check_rate_limit(
        db, client_ip, "login_attempt",
        max_attempts=settings.login_max_attempts,
        window_minutes=settings.login_window_minutes
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Çok fazla giriş denemesi. {settings.login_window_minutes} dakika sonra tekrar deneyin."
        )
    
    user = await get_user_by_email(db, email)
    
    if not user:
        await increment_rate_limit(db, client_ip, "login_attempt", settings.login_window_minutes)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı",
            headers={"X-Remaining-Attempts": str(remaining)}
        )
    
    # Hesap kilitli mi kontrol et
    is_unlocked = await check_and_unlock_user(db, user)
    if not is_unlocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Hesabınız çok fazla başarısız deneme nedeniyle kilitlendi. {settings.account_lock_minutes} dakika sonra tekrar deneyin."
        )
    
    # Email doğrulanmış mı?
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email adresiniz doğrulanmamış. Önce kayıt işlemini tamamlayın."
        )
    
    # Şifre kontrolü
    if not verify_password(data.password, user.password_hash):
        await increment_rate_limit(db, client_ip, "login_attempt", settings.login_window_minutes)
        
        # Başarısız deneme sayısını artır
        user.failed_login_attempts += 1
        
        # Hesap kilitleme kontrolü
        if user.failed_login_attempts >= settings.max_failed_attempts_before_lock:
            await lock_user_account(db, user, settings.account_lock_minutes)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Hesabınız çok fazla başarısız deneme nedeniyle {settings.account_lock_minutes} dakika süreyle kilitlendi."
            )
        
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email veya şifre hatalı",
            headers={"X-Remaining-Attempts": str(remaining)}
        )
    
    # Email gönderim rate limit kontrolü
    allowed, _ = await check_rate_limit(
        db, email, "email_send",
        max_attempts=settings.email_max_sends,
        window_minutes=settings.email_window_minutes
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Bu email adresine çok fazla kod gönderildi. {settings.email_window_minutes} dakika sonra tekrar deneyin."
        )
    
    # Başarısız deneme sayısını sıfırla
    user.failed_login_attempts = 0
    await db.commit()
    
    # Login doğrulama kodu gönder
    code = await create_verification_code(db, email, VerificationType.LOGIN)
    await increment_rate_limit(db, email, "email_send", settings.email_window_minutes)
    
    email_sent = await send_verification_email(email, code)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email gönderilemedi. Lütfen tekrar deneyin."
        )
    
    # IP rate limit'i sıfırla (başarılı şifre girişi)
    await reset_rate_limit(db, client_ip, "login_attempt")
    
    return MessageResponse(message="Doğrulama kodu email adresinize gönderildi")


@router.post("/verify-login", response_model=TokenResponse)
async def verify_login(
    request: Request,
    data: VerifyLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login doğrulama kodunu kontrol et ve token döndür"""
    client_ip = get_client_ip(request)
    email = data.email.lower()
    
    # Rate limit kontrolü
    allowed, remaining = await check_rate_limit(
        db, client_ip, "verify_attempt",
        max_attempts=10, window_minutes=15
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla doğrulama denemesi. 15 dakika sonra tekrar deneyin."
        )
    
    user = await get_user_by_email(db, email)
    if not user:
        await increment_rate_limit(db, client_ip, "verify_attempt", 15)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kullanıcı bulunamadı"
        )
    
    is_valid = await verify_code(db, email, data.code, VerificationType.LOGIN)
    if not is_valid:
        await increment_rate_limit(db, client_ip, "verify_attempt", 15)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş doğrulama kodu"
        )
    
    # Rate limit'leri sıfırla
    await reset_rate_limit(db, client_ip, "verify_attempt")
    await reset_rate_limit(db, email, "email_send")
    
    # Token oluştur ve döndür
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Mevcut kullanıcı bilgisini döndür"""
    return current_user


@router.post("/resend-code", response_model=MessageResponse)
async def resend_verification_code(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Doğrulama kodunu yeniden gönder"""
    client_ip = get_client_ip(request)
    email = data.email.lower()
    
    # Email gönderim rate limit kontrolü
    allowed, remaining = await check_rate_limit(
        db, email, "email_send",
        max_attempts=settings.email_max_sends,
        window_minutes=settings.email_window_minutes
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Bu email adresine çok fazla kod gönderildi. {settings.email_window_minutes} dakika sonra tekrar deneyin.",
        )
    
    user = await get_user_by_email(db, email)
    if not user:
        # Güvenlik: Kullanıcı olmasa bile başarılı görünsün
        return MessageResponse(message="Eğer hesap varsa, doğrulama kodu gönderildi")
    
    # Şifre kontrolü
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Şifre hatalı"
        )
    
    # Doğrulama türünü belirle
    verification_type = VerificationType.REGISTER if not user.is_verified else VerificationType.LOGIN
    
    code = await create_verification_code(db, email, verification_type)
    await increment_rate_limit(db, email, "email_send", settings.email_window_minutes)
    
    await send_verification_email(email, code)
    
    return MessageResponse(
        message="Doğrulama kodu email adresinize gönderildi",
        remaining_attempts=remaining
    )
