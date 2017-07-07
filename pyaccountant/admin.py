from django.contrib import admin

from .models import Account, AccountType, Currency, Transaction, TransactionJournal


admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(Currency)
admin.site.register(TransactionJournal)
admin.site.register(AccountType)
