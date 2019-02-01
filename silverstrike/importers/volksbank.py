import csv
import datetime

from silverstrike.importers.import_statement import ImportStatement


def import_transactions(csv_path):
    lines = []
    with open(csv_path, encoding='latin-1') as csv_file:
        for line in csv.reader(csv_file, delimiter=';'):
            if len(line) < 7:
                continue
            try:
                amount = float(line[11].replace('.', '').replace(',', '.'))
                if line[12] == 'S':
                    amount = -amount
                lines.append(ImportStatement(
                    book_date=datetime.datetime.strptime(line[1], '%d.%m.%Y').date(),
                    transaction_date=datetime.datetime.strptime(line[0], '%d.%m.%Y').date(),
                    account=line[3],
                    notes=line[8],
                    iban=line[5],
                    amount=amount
                    ))
            except ValueError as e:
                # first line contains headers...
                print(e)
                pass
    return lines[1:-2]
