import httpx
from app.core.config import settings


async def send_verification_email(email: str, code: str) -> bool:
    """
    Mail doğrulama kodunu webhook üzerinden gönder.
    Make.com webhook'una POST request atar.
    """
    if not settings.email_webhook_url:
        print(f"[DEV] Email webhook URL tanımlı değil. Kod: {code} -> {email}")
        return True
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                settings.email_webhook_url,
                json={
                    "email": email,
                    "code": code
                }
            )
            
            if response.status_code in [200, 201, 202]:
                print(f"[EMAIL] Doğrulama kodu gönderildi: {email}")
                return True
            else:
                print(f"[EMAIL] Webhook hatası: {response.status_code} - {response.text}")
                return False
                
    except httpx.TimeoutException:
        print(f"[EMAIL] Webhook timeout: {email}")
        return False
    except Exception as e:
        print(f"[EMAIL] Webhook hatası: {e}")
        return False
