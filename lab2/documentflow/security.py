from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import hashlib, os

@dataclass
class PasswordPolicy:
    min_length: int = 8
    require_digit: bool = True
    def validate(self, password: str) -> bool:
        if len(password) < self.min_length:
            return False
        if self.require_digit and not any(ch.isdigit() for ch in password):
            return False
        return True

@dataclass
class Session:
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    def is_active(self, moment: datetime) -> bool:
        return self.created_at <= moment <= self.expires_at

@dataclass
class Token:
    value: str
    issued_at: datetime
    @staticmethod
    def generate() -> "Token":
        raw = os.urandom(16).hex()
        return Token(value=hashlib.sha256(raw.encode()).hexdigest(), issued_at=datetime.utcnow())

@dataclass
class QuotaManager:
    max_bytes: int
    used_bytes: int = 0
    def can_allocate(self, size: int) -> bool:
        return self.used_bytes + size <= self.max_bytes
    def allocate(self, size: int) -> None:
        if not self.can_allocate(size):
            from .exceptions import StorageLimitExceededError
            raise StorageLimitExceededError("Недостаточно квоты")
        self.used_bytes += size
