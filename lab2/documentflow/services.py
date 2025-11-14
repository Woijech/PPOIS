from __future__ import annotations
from dataclasses import dataclass
from typing import List, Iterable, Dict
from .core import DocumentRepositoryProtocol, NotifierProtocol, PaymentProcessorProtocol
from .documents import Document, InvoiceDocument, DocumentAttachment, DocumentRegistry
from .exceptions import DocumentNotFoundError, AccessDeniedError, AuthFailedError
from .workflow import ApprovalRoute, ApprovalStep, WorkflowState
from .users import User
from .security import PasswordPolicy, Token
from .storage import DocumentStorage

@dataclass
class InMemoryDocumentRepository(DocumentRepositoryProtocol):
    storage: DocumentStorage
    def save(self, doc: Document) -> None:
        self.storage.save(doc)
    def get(self, number: str) -> Document | None:
        try:
            return self.storage.get(number)
        except DocumentNotFoundError:
            return None
    def exists(self, number: str) -> bool:
        return self.storage.exists(number)
    def search(self, query: str) -> Iterable[Document]:
        for d in list(self.storage._docs.values()):  # type: ignore[attr-defined]
            if query.lower() in d.title.lower() or query.lower() in d.number.lower():
                yield d

@dataclass
class ConsoleNotifier(NotifierProtocol):
    def notify(self, message: str) -> None:
        print(f"[NOTIFY] {message}")

@dataclass
class SearchService:
    repo: DocumentRepositoryProtocol
    def find(self, query: str) -> List[Document]:
        return list(self.repo.search(query))

@dataclass
class ValidationService:
    def validate(self, doc: Document) -> None:
        doc.validate()

@dataclass
class NotificationService:
    notifier: NotifierProtocol
    def send(self, message: str) -> None:
        self.notifier.notify(message)

@dataclass
class DocumentService:
    repo: DocumentRepositoryProtocol
    registry: DocumentRegistry
    validator: ValidationService
    notifier: NotificationService

    def register(self, doc: Document) -> None:
        self.registry.register(doc.number)
        self.validator.validate(doc)
        self.repo.save(doc)
        self.notifier.send(f"Документ зарегистрирован: {doc.number}")

    def add_attachment(self, number: str, att: DocumentAttachment) -> None:
        doc = self.require(number)
        doc.add_attachment(att)
        self.repo.save(doc)

    def send_for_approval(self, number: str, route: ApprovalRoute) -> None:
        doc = self.require(number)
        doc.approval_route = route
        doc.status = WorkflowState.IN_REVIEW
        self.repo.save(doc)
        self.notifier.send(f"Документ {number} отправлен на согласование")

    def sign(self, number: str, user: User) -> None:
        doc = self.require(number)
        if user.is_blocked:
            raise AccessDeniedError("Пользователь заблокирован")
        doc.sign(user.id)
        self.repo.save(doc)

    def archive(self, number: str) -> None:
        doc = self.require(number)
        doc.archive()
        self.repo.save(doc)

    def require(self, number: str) -> Document:
        doc = self.repo.get(number)
        if not doc:
            raise DocumentNotFoundError(number)
        return doc

@dataclass
class ApprovalService:
    notifier: NotificationService
    def route_for_role(self, role_name: str) -> ApprovalRoute:
        steps = [ApprovalStep(name="Проверка", role_name=role_name)]
        return ApprovalRoute(name=f"route:{role_name}", steps=steps)
    def approve(self, doc: Document) -> None:
        doc.approve()
        self.notifier.send(f"Документ согласован: {doc.number}")

@dataclass
class PaymentService:
    processor: PaymentProcessorProtocol
    notifier: NotificationService
    def pay_invoice(self, invoice: InvoiceDocument, src: str, dst: str, amount: int) -> str:
        tx = self.processor.transfer(src, dst, amount)
        invoice.mark_paid()
        self.notifier.send(f"Оплата счёта {invoice.number} проведена: {tx}")
        return tx

@dataclass
class AuthService:
    users: Dict[str, str]
    policy: PasswordPolicy
    def login(self, login: str, password: str) -> Token:
        if login not in self.users:
            raise AuthFailedError("Пользователь не найден")
        if not self.policy.validate(password) or self.users[login] != password:
            raise AuthFailedError("Неверные учетные данные")
        return Token.generate()
