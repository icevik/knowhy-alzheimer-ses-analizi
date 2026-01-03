import jwt
import secrets
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.config import settings
from app.models.user import User
from app.models.email_verification import EmailVerification, VerificationType
from app.models.rate_limit import RateLimit


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Şifreyi bcrypt ile hashle"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Şifreyi doğrula"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, email: str) -> str:
    """JWT access token oluştur"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """JWT token'ı decode et"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def generate_verification_code() -> str:
    """6 haneli doğrulama kodu oluştur"""
    return str(secrets.randbelow(900000) + 100000)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Email ile kullanıcı bul"""
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def create_verification_code(
    db: AsyncSession, 
    email: str, 
    verification_type: VerificationType,
    expires_minutes: int = 10
) -> str:
    """Doğrulama kodu oluştur ve kaydet"""
    # Eski kodları sil
    await db.execute(
        delete(EmailVerification).where(
            EmailVerification.email == email.lower(),
            EmailVerification.verification_type == verification_type
        )
    )
    
    code = generate_verification_code()
    verification = EmailVerification(
        email=email.lower(),
        code=code,
        verification_type=verification_type,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    )
    db.add(verification)
    await db.commit()
    return code


async def verify_code(
    db: AsyncSession,
    email: str,
    code: str,
    verification_type: VerificationType
) -> bool:
    """Doğrulama kodunu kontrol et"""
    result = await db.execute(
        select(EmailVerification).where(
            EmailVerification.email == email.lower(),
            EmailVerification.code == code,
            EmailVerification.verification_type == verification_type,
            EmailVerification.used == False,
            EmailVerification.expires_at > datetime.now(timezone.utc)
        )
    )
    verification = result.scalar_one_or_none()
    
    if verification:
        verification.used = True
        await db.commit()
        return True
    return False


# Rate Limiting fonksiyonları
async def check_rate_limit(
    db: AsyncSession,
    identifier: str,
    action_type: str,
    max_attempts: int,
    window_minutes: int
) -> tuple[bool, int]:
    """
    Rate limit kontrolü yap.
    Returns: (izin_var_mı, kalan_deneme_sayısı)
    """
    window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    
    result = await db.execute(
        select(RateLimit).where(
            RateLimit.identifier == identifier,
            RateLimit.action_type == action_type,
            RateLimit.first_attempt_at > window_start
        )
    )
    rate_limit = result.scalar_one_or_none()
    
    if not rate_limit:
        return True, max_attempts - 1
    
    if rate_limit.attempt_count >= max_attempts:
        return False, 0
    
    return True, max_attempts - rate_limit.attempt_count - 1


async def increment_rate_limit(
    db: AsyncSession,
    identifier: str,
    action_type: str,
    window_minutes: int
) -> None:
    """Rate limit sayacını artır"""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    
    result = await db.execute(
        select(RateLimit).where(
            RateLimit.identifier == identifier,
            RateLimit.action_type == action_type,
            RateLimit.first_attempt_at > window_start
        )
    )
    rate_limit = result.scalar_one_or_none()
    
    if rate_limit:
        rate_limit.attempt_count += 1
        rate_limit.last_attempt_at = datetime.now(timezone.utc)
    else:
        # Eski kayıtları temizle
        await db.execute(
            delete(RateLimit).where(
                RateLimit.identifier == identifier,
                RateLimit.action_type == action_type
            )
        )
        rate_limit = RateLimit(
            identifier=identifier,
            action_type=action_type,
            attempt_count=1
        )
        db.add(rate_limit)
    
    await db.commit()


async def reset_rate_limit(
    db: AsyncSession,
    identifier: str,
    action_type: str
) -> None:
    """Rate limit sayacını sıfırla (başarılı işlem sonrası)"""
    await db.execute(
        delete(RateLimit).where(
            RateLimit.identifier == identifier,
            RateLimit.action_type == action_type
        )
    )
    await db.commit()


async def lock_user_account(db: AsyncSession, user: User, lock_minutes: int = 60) -> None:
    """Kullanıcı hesabını kilitle"""
    user.is_locked = True
    user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=lock_minutes)
    await db.commit()


async def check_and_unlock_user(db: AsyncSession, user: User) -> bool:
    """Kullanıcı hesabını kontrol et, süresi dolduysa kilidi aç"""
    if not user.is_locked:
        return True
    
    if user.locked_until and user.locked_until < datetime.now(timezone.utc):
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        await db.commit()
        return True
    
    return False
