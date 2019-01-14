
import logging

from ofxparse import OfxParser

from silverstrike.importers.import_statement import ImportStatement


logger = logging.getLogger(__name__)

DATE_FORMAT = "%m/%d/%Y"


def import_csv(ofx_path):
    transactions = []
    with open(ofx_path, encoding='latin-1') as ofx_file:
        logger.info("Opening ofx file %s", ofx_path)
        try:
            ofx = OfxParser.parse(ofx_file)
            for transaction in ofx.account.statement.transactions:
                try:
                    transaction_time = transaction.date
                    transactions.append(ImportStatement(
                        notes=transaction.payee,
                        book_date=transaction_time,
                        transaction_date=transaction_time,
                        amount=transaction.amount
                        ))
                except ValueError:
                    logger.error("Cannot import transaction: {}".format(transaction))
                    pass
        except ValueError:
            logger.error("Failed to import all transactions! Wrong file format?")

    return transactions
