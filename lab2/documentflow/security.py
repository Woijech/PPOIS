from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import hashlib, os

@dataclass
class PasswordPolicy:
    min_length: int = 8
    require_digit: bool = True
    require_uppercase: bool = False
    require_special: bool = False
    
    def validate(self, password: str) -> bool:
        if len(password) < self.min_length:
            return False
        if self.require_digit and not any(ch.isdigit() for ch in password):
            return False
        if self.require_uppercase and not any(ch.isupper() for ch in password):
            return False
        if self.require_special and not any(ch in "!@#$%^&*()_+-=[]{}|;:,.<>?" for ch in password):
            return False
        return True
    
    def get_strength_score(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        score = 0
        if len(password) >= self.min_length:
            score += 25
        if any(ch.isdigit() for ch in password):
            score += 25
        if any(ch.isupper() for ch in password):
            score += 25
        if any(ch in "!@#$%^&*()_+-=[]{}|;:,.<>?" for ch in password):
            score += 25
        return score

@dataclass
class Session:
    user_id: str
    token: str
    created_at: datetime
    expires_at: datetime
    ip_address: str = ""
    is_terminated: bool = False
    
    def is_active(self, moment: datetime) -> bool:
        return not self.is_terminated and self.created_at <= moment <= self.expires_at
    
    def terminate(self) -> None:
        """Terminate this session"""
        self.is_terminated = True
    
    def extend(self, hours: int) -> None:
        """Extend session expiration time"""
        from datetime import timedelta
        self.expires_at = self.expires_at + timedelta(hours=hours)

@dataclass
class Token:
    value: str
    issued_at: datetime
    expires_at: datetime | None = None
    
    @staticmethod
    def generate() -> "Token":
        raw = os.urandom(16).hex()
        return Token(value=hashlib.sha256(raw.encode()).hexdigest(), issued_at=datetime.utcnow())
    
    def is_expired(self, moment: datetime) -> bool:
        """Check if token is expired"""
        if not self.expires_at:
            return False
        return moment > self.expires_at
    
    def revoke(self) -> None:
        """Revoke token by setting expiration to now"""
        self.expires_at = datetime.utcnow()

@dataclass
class QuotaManager:
    max_bytes: int
    used_bytes: int = 0
    warning_threshold: int = 0
    
    def can_allocate(self, size: int) -> bool:
        return self.used_bytes + size <= self.max_bytes
    
    def allocate(self, size: int) -> None:
        if not self.can_allocate(size):
            from .exceptions import StorageLimitExceededError
            raise StorageLimitExceededError("Недостаточно квоты")
        self.used_bytes += size
    
    def deallocate(self, size: int) -> None:
        """Free up quota space"""
        self.used_bytes = max(0, self.used_bytes - size)
    
    def get_usage_percentage(self) -> float:
        """Get quota usage as percentage"""
        if self.max_bytes == 0:
            return 0.0
        return (self.used_bytes / self.max_bytes) * 100
    
    def is_near_limit(self) -> bool:
        """Check if usage is near warning threshold"""
        if self.warning_threshold == 0:
            self.warning_threshold = int(self.max_bytes * 0.8)
        return self.used_bytes >= self.warning_threshold
