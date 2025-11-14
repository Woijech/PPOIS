from __future__ import annotations
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol, runtime_checkable, Optional, Iterable


@dataclass(kw_only=True)
class BaseEntity:
    created_at: datetime = field(default_factory=datetime.utcnow, init=False)
    updated_at: datetime = field(default_factory=datetime.utcnow, init=False)

    def touch(self) -> None:
        self.updated_at = datetime.utcnow()


class IdentifiableMixin:
    id: str

    def identity(self) -> str:
        return self.id


class TimestampMixin:
    created_at: datetime
    updated_at: datetime


class Validatable(ABC):
    def validate(self) -> None: ...


class Approvable(ABC):
    def approve(self) -> None: ...


class Signable(ABC):
    def sign(self, user_id: str) -> None: ...


class Storable(ABC):
    def store(self) -> str: ...


@runtime_checkable
class NotifierProtocol(Protocol):
    def notify(self, message: str) -> None: ...


@runtime_checkable
class PaymentProcessorProtocol(Protocol):
    def transfer(self, src_account: str, dst_account: str, amount: int) -> str: ...


class DocumentLike(Protocol):
    number: str
    title: str

    def validate(self) -> None: ...


@runtime_checkable
class DocumentRepositoryProtocol(Protocol):
    def save(self, doc: "DocumentLike") -> None: ...

    def get(self, number: str) -> Optional["DocumentLike"]: ...

    def exists(self, number: str) -> bool: ...

    def search(self, query: str) -> Iterable["DocumentLike"]: ...
