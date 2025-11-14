from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict
from .core import BaseEntity, IdentifiableMixin, Validatable, Approvable, Signable
from .exceptions import InvalidDocumentStatusError, InvalidSignatureError, VersionConflictError
from .users import User, Organization, Department
from .workflow import ApprovalRoute, WorkflowState

@dataclass
class DocumentMetadata:
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)

@dataclass
class DocumentAttachment:
    filename: str
    content_type: str
    size: int
    checksum: str

@dataclass
class DocumentVersion:
    number: int
    content: str
    created_at: datetime
    author_id: str

@dataclass
class Signature:
    user_id: str
    certificate_id: str
    signed_at: datetime

@dataclass
class DigitalCertificate:
    id: str
    subject: str
    valid_from: datetime
    valid_to: datetime
    def is_valid(self, moment: datetime) -> bool:
        return self.valid_from <= moment <= self.valid_to

@dataclass
class DocumentHistoryRecord:
    event: str
    actor_id: str
    occurred_at: datetime
    details: str = ""

@dataclass
class DocumentLock:
    owner_id: str
    acquired_at: datetime

@dataclass(kw_only=True)
class Document(IdentifiableMixin, Validatable, Approvable, Signable, BaseEntity):
    id: str
    number: str
    title: str
    author: User
    organization: Organization | None = None
    department: Department | None = None
    status: str = WorkflowState.NEW
    versions: List[DocumentVersion] = field(default_factory=list)
    attachments: List[DocumentAttachment] = field(default_factory=list)
    approval_route: ApprovalRoute | None = None
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    _lock: DocumentLock | None = None
    signatures: List[Signature] = field(default_factory=list)

    def validate(self) -> None:
        if not self.title or not self.number:
            raise ValueError("title и number обязательны")

    def add_version(self, content: str, author_id: str) -> DocumentVersion:
        v = DocumentVersion(
            number=len(self.versions) + 1,
            content=content,
            created_at=datetime.utcnow(),
            author_id=author_id,
        )
        self.versions.append(v)
        self.touch()
        return v

    def add_attachment(self, attachment: DocumentAttachment) -> None:
        self.attachments.append(attachment)
        self.touch()

    def lock(self, user_id: str) -> None:
        if self._lock and self._lock.owner_id != user_id:
            raise VersionConflictError("Документ уже заблокирован другим пользователем")
        self._lock = DocumentLock(owner_id=user_id, acquired_at=datetime.utcnow())

    def unlock(self, user_id: str) -> None:
        if self._lock and self._lock.owner_id != user_id:
            raise VersionConflictError("Разблокировать может только владелец блокировки")
        self._lock = None

    def approve(self) -> None:
        if self.status not in (WorkflowState.NEW, WorkflowState.IN_REVIEW):
            raise InvalidDocumentStatusError("Нельзя согласовать в текущем статусе")
        self.status = WorkflowState.APPROVED
        self.touch()

    def sign(self, user_id: str) -> None:
        if not self.versions:
            raise InvalidSignatureError("Нечего подписывать: нет версий")
        self.signatures.append(Signature(user_id=user_id, certificate_id="cert", signed_at=datetime.utcnow()))
        self.touch()

    def archive(self) -> None:
        if self.status == WorkflowState.ARCHIVED:
            raise InvalidDocumentStatusError("Документ уже в архиве")
        self.status = WorkflowState.ARCHIVED
        self.touch()

    def restore(self) -> None:
        if self.status != WorkflowState.ARCHIVED:
            raise InvalidDocumentStatusError("Можно восстановить только из архива")
        self.status = WorkflowState.NEW
        self.touch()

@dataclass
class IncomingDocument(Document):
    sender: str = ""
    def approve(self) -> None:
        super().approve()

@dataclass
class OutgoingDocument(Document):
    recipient: str = ""
    def approve(self) -> None:
        super().approve()

@dataclass
class ContractDocument(Document):
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    total_amount: int = 0
    def validate(self) -> None:
        super().validate()
        if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
            raise ValueError("Дата окончания раньше даты начала")

@dataclass
class InvoiceDocument(Document):
    amount_due: int = 0
    due_date: datetime | None = None
    paid: bool = False
    def mark_paid(self) -> None:
        self.paid = True
        self.touch()

@dataclass
class OrderDocument(Document):
    items: List[str] = field(default_factory=list)

@dataclass
class DocumentRegistry:
    numbers: set[str] = field(default_factory=set)
    def register(self, number: str) -> None:
        from .exceptions import DuplicateDocumentError
        if number in self.numbers:
            raise DuplicateDocumentError(f"Номер {number} уже существует")
        self.numbers.add(number)
    def contains(self, number: str) -> bool:
        return number in self.numbers
