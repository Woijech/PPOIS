from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime
from .exceptions import PaymentOperationError

class Currency:
    BYN = "BYN"
    USD = "USD"
    EUR = "EUR"

@dataclass
class Account:
    number: str
    currency: str = Currency.BYN
    balance: int = 0
    is_frozen: bool = False
    overdraft_limit: int = 0
    
    def debit(self, amount: int) -> None:
        if self.is_frozen:
            raise PaymentOperationError("Счет заморожен")
        if amount < 0:
            raise PaymentOperationError("Отрицательная сумма")
        if self.balance + self.overdraft_limit < amount:
            raise PaymentOperationError("Недостаточно средств")
        self.balance -= amount
    
    def credit(self, amount: int) -> None:
        if self.is_frozen:
            raise PaymentOperationError("Счет заморожен")
        if amount < 0:
            raise PaymentOperationError("Отрицательная сумма")
        self.balance += amount
    
    def freeze(self) -> None:
        """Freeze account operations"""
        self.is_frozen = True
    
    def unfreeze(self) -> None:
        """Unfreeze account operations"""
        self.is_frozen = False
    
    def set_overdraft_limit(self, limit: int) -> None:
        """Set overdraft limit for the account"""
        if limit < 0:
            raise PaymentOperationError("Отрицательный овердрафт")
        self.overdraft_limit = limit
    
    def get_available_balance(self) -> int:
        """Get available balance including overdraft"""
        return self.balance + self.overdraft_limit

@dataclass
class Transaction:
    id: str
    src: str
    dst: str
    amount: int
    created_at: datetime
    status: str = "completed"
    description: str = ""
    
    def cancel(self) -> None:
        """Mark transaction as cancelled"""
        self.status = "cancelled"
    
    def is_completed(self) -> bool:
        """Check if transaction is completed"""
        return self.status == "completed"

@dataclass
class PaymentOrder:
    invoice_number: str
    src_account: str
    dst_account: str
    amount: int
    currency: str = Currency.BYN
    priority: int = 0
    scheduled_date: datetime | None = None
    
    def is_high_priority(self) -> bool:
        """Check if this is a high priority payment"""
        return self.priority > 5
    
    def is_scheduled(self) -> bool:
        """Check if payment is scheduled for future"""
        if not self.scheduled_date:
            return False
        return self.scheduled_date > datetime.utcnow()

@dataclass
class BalanceChecker:
    min_balance: int = 0
    
    def ensure_same_currency(self, a: Account, b: Account) -> None:
        if a.currency != b.currency:
            raise PaymentOperationError("Несовпадение валюты счетов")
    
    def check_sufficient_funds(self, account: Account, amount: int) -> bool:
        """Check if account has sufficient funds"""
        return account.get_available_balance() >= amount
    
    def check_min_balance(self, account: Account) -> bool:
        """Check if account meets minimum balance requirement"""
        return account.balance >= self.min_balance

@dataclass
class InMemoryPaymentProcessor:
    accounts: Dict[str, Account]
    balance_checker: BalanceChecker
    transactions: List[Transaction] = field(default_factory=list)
    daily_limit: int = 1000000
    
    def transfer(self, src_account: str, dst_account: str, amount: int) -> str:
        src = self.accounts[src_account]
        dst = self.accounts[dst_account]
        self.balance_checker.ensure_same_currency(src, dst)
        src.debit(amount)
        dst.credit(amount)
        tx_id = f"tx-{len(self.transactions)+1}"
        self.transactions.append(Transaction(id=tx_id, src=src_account, dst=dst_account, amount=amount, created_at=datetime.utcnow()))
        return tx_id
    
    def get_account_balance(self, account_number: str) -> int:
        """Get account balance"""
        return self.accounts[account_number].balance
    
    def get_transaction_history(self, account_number: str) -> List[Transaction]:
        """Get transaction history for account"""
        return [tx for tx in self.transactions if tx.src == account_number or tx.dst == account_number]
    
    def check_daily_limit(self, amount: int) -> bool:
        """Check if amount is within daily limit"""
        return amount <= self.daily_limit
