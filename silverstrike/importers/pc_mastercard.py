import csv
import datetime

from silverstrike.importers.import_statement import ImportStatement

import logging

logger = logging.getLogger(__name__)


def import_csv(csv_path):
    lines = []
    with open(csv_path, encoding='latin-1') as csv_file:
        logger.info("Opened csv file %s", csv_path)
        csviter = csv.reader(csv_file, delimiter=',')
        next(csviter)  # First line is header
        for line in csviter:
            logger.info("Line %s", line)
            try:
                transaction_time = datetime.datetime.strptime(line[2] + ' ' + line[3], '%m/%d/%Y %I:%M %p')
                lines.append(ImportStatement(
                    notes=line[0],
                    account=line[1],
                    book_date=transaction_time,
                    transaction_date=transaction_time,
                    amount=-float(line[4])
                    ))
            except ValueError as e:
                logger.error("Error" + e)
                pass

    return lines
