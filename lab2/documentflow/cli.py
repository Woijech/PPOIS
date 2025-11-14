from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from .users import User, Role, Organization, Department
from .documents import IncomingDocument, InvoiceDocument, DocumentRegistry, DocumentAttachment
from .storage import StorageLocation, DocumentStorage
from .security import QuotaManager, PasswordPolicy
from .payments import Account, BalanceChecker, InMemoryPaymentProcessor
from .services import InMemoryDocumentRepository, ConsoleNotifier, NotificationService, ValidationService, DocumentService, ApprovalService, PaymentService, AuthService
from .workflow import ApprovalStep, ApprovalRoute

@dataclass
class DemoContext:
    repo: InMemoryDocumentRepository
    storage: DocumentStorage
    doc_service: DocumentService
    appr_service: ApprovalService
    pay_service: PaymentService
    auth: AuthService

def build_demo() -> DemoContext:
    loc = StorageLocation(name="local", base_path="/tmp/docs")
    quota = QuotaManager(max_bytes=10_000_000)
    storage = DocumentStorage(location=loc, quota=quota)
    repo = InMemoryDocumentRepository(storage=storage)
    notifier = ConsoleNotifier()
    notify = NotificationService(notifier=notifier)
    validator = ValidationService()
    registry = DocumentRegistry()
    doc_service = DocumentService(repo=repo, registry=registry, validator=validator, notifier=notify)
    appr_service = ApprovalService(notifier=notify)

    accounts: Dict[str, Account] = {
        "A": Account(number="A", balance=10000),
        "B": Account(number="B", balance=2000),
    }
    processor = InMemoryPaymentProcessor(accounts=accounts, balance_checker=BalanceChecker())
    pay_service = PaymentService(processor=processor, notifier=notify)
    auth = AuthService(users={"admin": "pass1234"}, policy=PasswordPolicy())
    return DemoContext(repo=repo, storage=storage, doc_service=doc_service, appr_service=appr_service, pay_service=pay_service, auth=auth)

def run_demo() -> None:
    ctx = build_demo()
    role_reviewer = Role(name="REVIEWER", permissions={"approve"})
    org = Organization(name="ООО Ромашка", inn="7711111111")
    dep = Department(name="Бухгалтерия", cost_center="100-200")
    user = User(id="u1", login="admin", display_name="Администратор", roles=[role_reviewer], org=org, department=dep)

    incoming = IncomingDocument(id="d1", number="IN-001", title="Письмо", author=user, organization=org, department=dep)
    invoice = InvoiceDocument(id="d2", number="INV-001", title="Счёт на оплату", author=user, organization=org, amount_due=1500)

    ctx.doc_service.register(incoming)
    ctx.doc_service.register(invoice)

    route = ApprovalRoute(name="basic", steps=[ApprovalStep(name="Проверка", role_name=role_reviewer.name)])
    ctx.doc_service.send_for_approval(number="IN-001", route=route)
    ctx.appr_service.approve(incoming)

    incoming.add_version("v1", user.id)
    ctx.doc_service.sign("IN-001", user)

    try:
        ctx.doc_service.sign("INV-404", user)
    except Exception as e:
        print("Ожидаемая ошибка:", type(e).__name__, str(e))

    ctx.doc_service.add_attachment("IN-001", DocumentAttachment(filename="note.txt", content_type="text/plain", size=32, checksum="abc"))
    ctx.doc_service.archive("IN-001")

    invoice.add_version("v1", user.id)
    tx = ctx.pay_service.pay_invoice(invoice, src="A", dst="B", amount=1500)
    print("TX:", tx)
    print("Баланс A:", ctx.pay_service.processor.accounts["A"].balance)  # type: ignore[attr-defined]
    print("Баланс B:", ctx.pay_service.processor.accounts["B"].balance)  # type: ignore[attr-defined]

if __name__ == "__main__":
    run_demo()
