from decimal import Decimal
from enum import Enum


class TransactionType(Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    DISPUTE = 'dispute'
    RESOLVE = 'resolve'
    CHARGEBACK = 'chargeback'


class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.available = Decimal('0.0000')
        self.total = Decimal('0.0000')
        self.held = Decimal('0.0000')
        self.locked = False

        self.deposits = {}
        self.disputes = {}

    @property
    def info(self):
        return (
            f'{self.client_id},{self.available},{self.held},{self.total:},'
            f'{self.locked}'.lower()
        )

    def _process_deposit(self, tx_id, amount: Decimal):
        self.available += amount
        self.total += amount
        self.deposits[tx_id] = amount

    def _process_withdraw(self, tx_id, amount: Decimal):
        if self.available < amount:
            return

        self.available -= amount
        self.total -= amount

    def _process_dispute(self, tx_id, amount: Decimal):
        if tx_id not in self.deposits:
            return

        amount = self.deposits[tx_id]
        self.available -= amount
        self.held += amount
        self.disputes[tx_id] = amount

    def _process_resolve(self, tx_id, amount: Decimal):
        if tx_id not in self.disputes:
            return

        amount = self.disputes.pop(tx_id)
        self.available += amount
        self.held -= amount

    def _process_chargeback(self, tx_id, amount: Decimal):
        if tx_id not in self.disputes:
            return

        amount = self.disputes.pop(tx_id)
        self.held -= amount
        self.total -= amount
        self.locked = True

    def process_transaction(self, transaction_type, tx_id, amount):
        if self.locked:
            return

        if amount is not None:
            amount = Decimal(str(amount)).quantize(Decimal('.0001'))

        processors = {
            TransactionType.DEPOSIT: self._process_deposit,
            TransactionType.WITHDRAWAL: self._process_withdraw,
            TransactionType.DISPUTE: self._process_dispute,
            TransactionType.RESOLVE: self._process_resolve,
            TransactionType.CHARGEBACK: self._process_chargeback,
        }

        processors[transaction_type](tx_id=tx_id, amount=amount)
