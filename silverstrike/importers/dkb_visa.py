import csv

from silverstrike.importers.import_statement import ImportStatement


def import_csv(csv_path):
    lines = []
    with open(csv_path, encoding='latin-1') as csv_file:
        for line in csv.reader(csv_file, delimiter=';'):
            if len(line) < 6:
                continue
            lines.append(ImportStatement(
                bookDate=line[1],
                documentDate=line[2],
                notes=line[3],
                amount=line[4].replace('.', '').replace(',', '.')
                ))
    return lines[1:]
