class ImportStatement(object):
    account = ''
    book_date = ''
    transaction_date = ''
    amount = 0
    notes = ''
    iban = ''

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        self.transaction_date = self.transaction_date or self.book_date
