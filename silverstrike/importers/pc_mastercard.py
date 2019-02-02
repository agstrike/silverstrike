import csv
import datetime
import logging

from silverstrike.importers.import_statement import ImportStatement


logger = logging.getLogger(__name__)


def import_transactions(csv_path):
    lines = []
    with open(csv_path) as csv_file:
        logger.info('Opened csv file %s', csv_path)
        csviter = csv.reader(csv_file, delimiter=',')
        next(csviter)  # First line is header
        for line in csviter:
            logger.info('Line %s', line)
            try:
                transaction_time = datetime.datetime.strptime(line[2], '%m/%d/%Y').date()
                lines.append(ImportStatement(
                    notes=line[0],
                    account=line[1],
                    book_date=transaction_time,
                    transaction_date=transaction_time,
                    amount=-float(line[4])
                    ))
            except ValueError as e:
                logger.error('Error' + e)
                pass

    return lines
