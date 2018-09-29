import csv

from silverstrike.importers.import_statement import ImportStatement


def import_csv(csv_path):
    lines = []
    with open(csv_path, encoding='latin-1') as csv_file:
        for line in csv.reader(csv_file, delimiter=';'):
            if len(line) < 5:
                continue
            lines.append(ImportStatement(
                bookDate=line[1],
                documentDate=line[0],
                account=line[3],
                notes=line[4],
                iban=line[5],
                amount=line[7].replace('.', '').replace(',', '.')
                ))
    return lines[1:]
