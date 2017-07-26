from django.contrib import admin

from .models import (Account, AccountType, Category, CategoryGroup,
                     Transaction, TransactionJournal)


admin.site.register(Account)
admin.site.register(Transaction)
admin.site.register(TransactionJournal)
admin.site.register(AccountType)
admin.site.register(Category)
admin.site.register(CategoryGroup)
