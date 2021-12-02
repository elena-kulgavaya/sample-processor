import unittest

from decimal import Decimal

from client_entity import Client, TransactionType


class TransactionProcessorTests(unittest.TestCase):
    """
    This test suite is designed to verify the logic of processing transactions
    within single client.
    """
    def setUp(self) -> None:
        self.client = Client(client_id=1)

    def verify_client_state(self, available=0., held=0., total=0.,
                            locked=False):
        self.assertDictEqual(
            d1={
                'available': Decimal(available).quantize(Decimal('.0001')),
                'held': Decimal(held).quantize(Decimal('.0001')),
                'total': Decimal(total).quantize(Decimal('.0001')),
                'locked': locked
            },
            d2={
                'available': self.client.available,
                'held': self.client.held,
                'total': self.client.total,
                'locked': self.client.locked,
            },
        )

    def test_deposit(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 13.32)
        self.verify_client_state(available=13.32, total=13.32)

    def test_withdrawal(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 10.12)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 5.01)
        self.verify_client_state(available=5.11, total=5.11)

    def test_withdrawal_all_funds(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 8.13)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 8.13)
        self.verify_client_state()

    def test_withdrawal_ignored_insufficient_funds(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 3.2)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 3.201)
        self.verify_client_state(available=3.2, total=3.2)

    def test_withdrawal_ignored_for_held_funds(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 11.1)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 7.56)
        self.verify_client_state(held=11.1, total=11.1)

    def test_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 10.01)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.verify_client_state(held=10.01, total=10.01)

    def test_dispute_one_of_transactions(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 5.14)
        self.client.process_transaction(TransactionType.DEPOSIT, 2, 3.22)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.verify_client_state(available=3.22, held=5.14, total=8.36)

    def test_dispute_of_withdrawal_amount(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 46.8)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 10.8)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.verify_client_state(available=-10.8, held=46.8, total=36)

    def test_dispute_not_existing_transactions(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 18.1)
        self.client.process_transaction(TransactionType.DISPUTE, 2, None)
        self.verify_client_state(available=18.1, total=18.1)

    def test_dispute_ignored_for_non_deposit_transaction(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 8.88)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 1.01)
        self.client.process_transaction(TransactionType.DISPUTE, 2, None)
        self.verify_client_state(available=7.87, total=7.87)

    def test_resolve_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 5.1)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.RESOLVE, 1, None)
        self.verify_client_state(available=5.1, total=5.1)

    def test_resolve_ignored_non_existing_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 3)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.RESOLVE, 2, None)
        self.verify_client_state(held=3, total=3)

    def test_resolve_ignored_non_disputed_transaction(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 4.4)
        self.client.process_transaction(TransactionType.RESOLVE, 1, None)
        self.verify_client_state(available=4.4, total=4.4)

    def test_chargeback_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 9.0)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.CHARGEBACK, 1, None)
        self.verify_client_state(locked=True)

    def test_chargeback_ignored_non_existing_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 77.11)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.CHARGEBACK, 2, None)
        self.verify_client_state(held=77.11, total=77.11)

    def test_chargeback_ignored_non_disputed_transaction(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 19.09)
        self.client.process_transaction(TransactionType.CHARGEBACK, 1, None)
        self.verify_client_state(available=19.09, total=19.09)

    def test_chargeback_ignores_next_transactions(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 9.0)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.CHARGEBACK, 1, None)
        self.client.process_transaction(TransactionType.DEPOSIT, 2, 10.01)
        self.verify_client_state(locked=True)

    def test_chargeback_ignored_for_resolved_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 11.21)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.RESOLVE, 1, None)
        self.client.process_transaction(TransactionType.CHARGEBACK, 1, None)
        self.verify_client_state(available=11.21, total=11.21)

    def test_resolve_ignored_for_charged_back_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 11.21)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.CHARGEBACK, 1, None)
        self.client.process_transaction(TransactionType.RESOLVE, 1, None)
        self.verify_client_state(locked=True)

    def test_dispute_resolved_dispute(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 2.71)
        self.client.process_transaction(TransactionType.DEPOSIT, 2, 15.6)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client.process_transaction(TransactionType.RESOLVE, 1, None)
        self.client.process_transaction(TransactionType.DISPUTE, 1, None)
        self.verify_client_state(available=15.6, held=2.71, total=18.31)

    def test_rounding_deposit(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 10.21346)
        self.verify_client_state(available=10.2135, total=10.2135)

    def test_rounding_withdrawal(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 10.0)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 2, 5.23122)
        self.verify_client_state(available=4.7688, total=4.7688)

    def test_rounding_before_calculations(self):
        self.client.process_transaction(TransactionType.DEPOSIT, 1, 7.14246)
        self.client.process_transaction(TransactionType.DEPOSIT, 2, 1.92179)
        self.client.process_transaction(TransactionType.WITHDRAWAL, 3, 3.89101)
        self.verify_client_state(available=5.1733, total=5.1733)


class MultiClientTests(unittest.TestCase):
    """
    The test suite executes the client processor against mutability to verify
    data from different clients is not affecting each other
    Though the test verification is performed in two steps, we can assume
    that the failure can only be the result of mutability issue, due to the
    execution of the transaction processing tests above.
    Same transaction id's are being used for purpose - to validate the
    data storage is not shared between clients (won't be moved to the
    class level vs object level in the future)
    """
    def setUp(self) -> None:
        self.client_a = Client(client_id=1)
        self.client_b = Client(client_id=2)

    def verify_client_state(self, client, available=0., held=0., total=0.,
                             locked=False):
        self.assertDictEqual(
            d1={
                'available': Decimal(available).quantize(Decimal('.0001')),
                'held': Decimal(held).quantize(Decimal('.0001')),
                'total': Decimal(total).quantize(Decimal('.0001')),
                'locked': locked
            },
            d2={
                'available': client.available,
                'held': client.held,
                'total': client.total,
                'locked': client.locked,
            },
        )

    def test_deposits(self):
        self.client_a.process_transaction(TransactionType.DEPOSIT, 1, 1.02)
        self.client_b.process_transaction(TransactionType.DEPOSIT, 1, 500)
        self.verify_client_state(self.client_a, available=1.02, total=1.02)
        self.verify_client_state(self.client_b, available=500, total=500)

    def test_withdrawals(self):
        self.client_a.process_transaction(TransactionType.DEPOSIT, 1, 100)
        self.client_a.process_transaction(TransactionType.WITHDRAWAL, 2, 50)
        self.client_b.process_transaction(TransactionType.DEPOSIT, 1, 200)
        self.client_b.process_transaction(TransactionType.WITHDRAWAL, 2, 30)
        self.verify_client_state(self.client_a, available=50, total=50)
        self.verify_client_state(self.client_b, available=170, total=170)

    def test_disputes(self):
        self.client_a.process_transaction(TransactionType.DEPOSIT, 1, 10)
        self.client_a.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client_b.process_transaction(TransactionType.DEPOSIT, 1, 20)
        self.client_b.process_transaction(TransactionType.DISPUTE, 1, None)
        self.verify_client_state(self.client_a, held=10, total=10)
        self.verify_client_state(self.client_b, held=20, total=20)

    def test_resolves(self):
        self.client_a.process_transaction(TransactionType.DEPOSIT, 1, 2.05)
        self.client_a.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client_a.process_transaction(TransactionType.RESOLVE, 1, None)
        self.client_b.process_transaction(TransactionType.DEPOSIT, 1, 76)
        self.client_b.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client_b.process_transaction(TransactionType.RESOLVE, 1, None)
        self.verify_client_state(self.client_a, available=2.05, total=2.05)
        self.verify_client_state(self.client_b, available=76, total=76)

    def test_resolve_and_chargeback(self):
        self.client_a.process_transaction(TransactionType.DEPOSIT, 1, 9.33)
        self.client_a.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client_a.process_transaction(TransactionType.RESOLVE, 1, None)
        self.client_b.process_transaction(TransactionType.DEPOSIT, 1, 15.4)
        self.client_b.process_transaction(TransactionType.DISPUTE, 1, None)
        self.client_b.process_transaction(TransactionType.CHARGEBACK, 1, None)
        self.verify_client_state(self.client_a, available=9.33, total=9.33)
        self.verify_client_state(self.client_b, locked=True)


class OutputFormatTests(unittest.TestCase):
    """
    Verifying types, order and values of the output data
    """
    def test_available(self):
        client = Client(client_id=1)
        client.available = Decimal('12.3121')
        self.assertEqual(client.info, '1,12.3121,0.0000,0.0000,false')

    def test_held(self):
        client = Client(client_id=6781)
        client.held = Decimal('1.3200')
        self.assertEqual(client.info, '6781,0.0000,1.3200,0.0000,false')

    def test_total(self):
        client = Client(client_id=78)
        client.total = Decimal('9.0927')
        self.assertEqual(client.info, '78,0.0000,0.0000,9.0927,false')

    def test_locked(self):
        client = Client(client_id=5)
        client.locked = True
        self.assertEqual(client.info, '5,0.0000,0.0000,0.0000,true')


if __name__ == '__main__':
    unittest.main()
