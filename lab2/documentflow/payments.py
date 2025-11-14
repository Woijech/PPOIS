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
    def debit(self, amount: int) -> None:
        if amount < 0:
            raise PaymentOperationError("Отрицательная сумма")
        if self.balance < amount:
            raise PaymentOperationError("Недостаточно средств")
        self.balance -= amount
    def credit(self, amount: int) -> None:
        if amount < 0:
            raise PaymentOperationError("Отрицательная сумма")
        self.balance += amount

@dataclass
class Transaction:
    id: str
    src: str
    dst: str
    amount: int
    created_at: datetime

@dataclass
class PaymentOrder:
    invoice_number: str
    src_account: str
    dst_account: str
    amount: int
    currency: str = Currency.BYN

@dataclass
class BalanceChecker:
    def ensure_same_currency(self, a: Account, b: Account) -> None:
        if a.currency != b.currency:
            raise PaymentOperationError("Несовпадение валюты счетов")

@dataclass
class InMemoryPaymentProcessor:
    accounts: Dict[str, Account]
    balance_checker: BalanceChecker
    transactions: List[Transaction] = field(default_factory=list)
    def transfer(self, src_account: str, dst_account: str, amount: int) -> str:
        src = self.accounts[src_account]
        dst = self.accounts[dst_account]
        self.balance_checker.ensure_same_currency(src, dst)
        src.debit(amount)
        dst.credit(amount)
        tx_id = f"tx-{len(self.transactions)+1}"
        self.transactions.append(Transaction(id=tx_id, src=src_account, dst=dst_account, amount=amount, created_at=datetime.utcnow()))
        return tx_id
