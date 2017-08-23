from django.contrib import admin

from .models import (Account, Category, ImportConfiguration, RecurringTransaction,
                     Transaction, TransactionJournal)

admin.site.register(TransactionJournal)
admin.site.register(Category)
admin.site.register(ImportConfiguration)
admin.site.register(RecurringTransaction)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('journal', 'account', 'opposing_account', 'amount')
    list_filter = ('account', 'opposing_account', 'journal__category')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('account_type',)
