import csv
import sys

from client_entity import Client, TransactionType


clients = {}


def process_record(client_id, tx_id, transaction_type, amount):
    if client_id not in clients:
        client = Client(client_id=client_id)
        clients[client_id] = client
    else:
        client = clients[client_id]

    client.process_transaction(
        transaction_type=transaction_type,
        tx_id=tx_id,
        amount=amount
    )


def process_document(document_name):
    with open(document_name) as transactions_file:
        reader = csv.DictReader(transactions_file)

        for row in reader:
            process_record(
                client_id=row['client'],
                transaction_type=TransactionType(row['type']),
                tx_id=row['tx'],
                amount=row['amount']
            )


def print_the_results():
    if not clients:
        return

    print('client,available,held,total,locked')

    for a_client in clients.values():
        print(a_client.info)


if __name__ == '__main__':
    process_document(sys.argv[1])
    print_the_results()
