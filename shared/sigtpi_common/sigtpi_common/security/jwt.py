from datetime import datetime, timedelta, timezone
import uuid
from jose import jwt
from pydantic import BaseModel

class TokenPayload(BaseModel):
    sub: str
    roles: list[str]
    exp: int
    iat: int
    jti: str
    service: str = "sigtpi"

def decode_token(token: str, secret_key: str, algorithm: str = "HS256") -> TokenPayload:
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    return TokenPayload(**payload)

def create_access_token(subject, roles: list[str], secret_key: str,
                         expires_minutes: int = 480, algorithm: str = "HS256") -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)
    return jwt.encode({"sub": str(subject), "roles": roles,
                        "exp": int(expire.timestamp()), "iat": int(now.timestamp()),
                        "jti": str(uuid.uuid4()), "service": "sigtpi"},
                       secret_key, algorithm=algorithm)
