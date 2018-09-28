import csv

def import_csv(csv_path):
    lines = []
    with open(csv_path) as csv_file:
        for line in csv.reader(csv_file, delimiter=';'):
            if len(line) < 5:
                continue
            lines.append([
                line[0], # documentDate
                line[1], # bookDate
                line[3], # account
                line[4], # notes
                line[7].replace('.', '').replace(',', '.') # amount
                ])
    return lines
