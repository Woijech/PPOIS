import unittest
from datetime import datetime, timedelta
from documentflow.payments import Account, BalanceChecker, InMemoryPaymentProcessor, Currency, Transaction, PaymentOrder
from documentflow.services import PaymentService, NotificationService, ConsoleNotifier
from documentflow.documents import InvoiceDocument
from documentflow.users import User
from documentflow.exceptions import PaymentOperationError

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
    
    def test_account_freeze_unfreeze(self):
        """Test account freeze and unfreeze operations"""
        account = Account(number="TEST", currency=Currency.BYN, balance=1000)
        
        # Test freeze
        account.freeze()
        self.assertTrue(account.is_frozen)
        
        # Test operations on frozen account
        with self.assertRaises(PaymentOperationError):
            account.debit(100)
        
        with self.assertRaises(PaymentOperationError):
            account.credit(100)
        
        # Test unfreeze
        account.unfreeze()
        self.assertFalse(account.is_frozen)
        
        # Operations should work after unfreeze
        account.debit(100)
        self.assertEqual(account.balance, 900)
        
        account.credit(200)
        self.assertEqual(account.balance, 1100)
    
    def test_account_overdraft(self):
        """Test account overdraft limit"""
        account = Account(number="OVER", currency=Currency.BYN, balance=100)
        
        # Test set_overdraft_limit
        account.set_overdraft_limit(500)
        self.assertEqual(account.overdraft_limit, 500)
        
        # Test negative overdraft limit
        with self.assertRaises(PaymentOperationError):
            account.set_overdraft_limit(-100)
        
        # Test get_available_balance
        self.assertEqual(account.get_available_balance(), 600)  # 100 + 500
        
        # Test debit with overdraft
        account.debit(400)
        self.assertEqual(account.balance, -300)
        
        # Test exceeding overdraft limit
        with self.assertRaises(PaymentOperationError):
            account.debit(400)  # Would need 700 total, but only 500 overdraft
    
    def test_account_negative_amount_errors(self):
        """Test account errors with negative amounts"""
        account = Account(number="NEG", currency=Currency.BYN, balance=1000)
        
        with self.assertRaises(PaymentOperationError):
            account.debit(-100)
        
        with self.assertRaises(PaymentOperationError):
            account.credit(-100)
    
    def test_transaction_methods(self):
        """Test transaction methods"""
        tx = Transaction(
            id="tx-123",
            src="A",
            dst="B",
            amount=500,
            created_at=datetime.utcnow(),
            status="completed"
        )
        
        # Test is_completed
        self.assertTrue(tx.is_completed())
        
        # Test cancel
        tx.cancel()
        self.assertEqual(tx.status, "cancelled")
        self.assertFalse(tx.is_completed())
    
    def test_payment_order_methods(self):
        """Test payment order methods"""
        # Test high priority order
        high_priority = PaymentOrder(
            invoice_number="INV-001",
            src_account="A",
            dst_account="B",
            amount=1000,
            priority=10
        )
        self.assertTrue(high_priority.is_high_priority())
        
        # Test low priority order
        low_priority = PaymentOrder(
            invoice_number="INV-002",
            src_account="A",
            dst_account="B",
            amount=500,
            priority=3
        )
        self.assertFalse(low_priority.is_high_priority())
        
        # Test scheduled payment
        future_date = datetime.utcnow() + timedelta(days=7)
        scheduled = PaymentOrder(
            invoice_number="INV-003",
            src_account="A",
            dst_account="B",
            amount=750,
            scheduled_date=future_date
        )
        self.assertTrue(scheduled.is_scheduled())
        
        # Test non-scheduled payment
        immediate = PaymentOrder(
            invoice_number="INV-004",
            src_account="A",
            dst_account="B",
            amount=250
        )
        self.assertFalse(immediate.is_scheduled())
    
    def test_balance_checker_methods(self):
        """Test balance checker methods"""
        checker = BalanceChecker(min_balance=100)
        
        # Test check_sufficient_funds
        account_ok = Account(number="OK", currency=Currency.BYN, balance=1000)
        self.assertTrue(checker.check_sufficient_funds(account_ok, 500))
        self.assertFalse(checker.check_sufficient_funds(account_ok, 1500))
        
        # Test check_min_balance
        account_high = Account(number="HIGH", currency=Currency.BYN, balance=500)
        self.assertTrue(checker.check_min_balance(account_high))
        
        account_low = Account(number="LOW", currency=Currency.BYN, balance=50)
        self.assertFalse(checker.check_min_balance(account_low))
    
    def test_payment_processor_methods(self):
        """Test payment processor additional methods"""
        accounts = {
            "A": Account(number="A", currency=Currency.BYN, balance=5000),
            "B": Account(number="B", currency=Currency.BYN, balance=1000)
        }
        processor = InMemoryPaymentProcessor(accounts=accounts, balance_checker=BalanceChecker())
        
        # Test get_account_balance
        self.assertEqual(processor.get_account_balance("A"), 5000)
        self.assertEqual(processor.get_account_balance("B"), 1000)
        
        # Make a transfer to create transaction history
        processor.transfer("A", "B", 1000)
        
        # Test get_transaction_history
        history_a = processor.get_transaction_history("A")
        self.assertEqual(len(history_a), 1)
        self.assertEqual(history_a[0].amount, 1000)
        
        history_b = processor.get_transaction_history("B")
        self.assertEqual(len(history_b), 1)
        
        # Test check_daily_limit
        processor_with_limit = InMemoryPaymentProcessor(
            accounts=accounts,
            balance_checker=BalanceChecker(),
            daily_limit=10000
        )
        self.assertTrue(processor_with_limit.check_daily_limit(5000))
        self.assertFalse(processor_with_limit.check_daily_limit(15000))

if __name__ == "__main__":
    unittest.main()
