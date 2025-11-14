import unittest
from documentflow.payments import Account, BalanceChecker, InMemoryPaymentProcessor, Currency
from documentflow.services import PaymentService, NotificationService, ConsoleNotifier
from documentflow.documents import InvoiceDocument
from documentflow.users import User

class TestPayments(unittest.TestCase):
    def test_transfer(self):
        accounts = {"A": Account(number="A", currency=Currency.BYN, balance=2000), "B": Account(number="B", currency=Currency.BYN, balance=0)}
        processor = InMemoryPaymentProcessor(accounts=accounts, balance_checker=BalanceChecker())
        payment_service = PaymentService(processor=processor, notifier=NotificationService(ConsoleNotifier()))
        user = User(id="u1", login="l", display_name="d")
        invoice = InvoiceDocument(id="i1", number="INV-1", title="inv", author=user, amount_due=1000)
        invoice.add_version("v1", user.id)
        tx = payment_service.pay_invoice(invoice, src="A", dst="B", amount=1000)
        self.assertTrue(tx.startswith("tx-"))
        self.assertTrue(invoice.paid)
        self.assertEqual(accounts["A"].balance, 1000)
        self.assertEqual(accounts["B"].balance, 1000)

if __name__ == "__main__":
    unittest.main()
