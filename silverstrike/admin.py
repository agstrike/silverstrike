from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext as _


from .models import (Account, Category, ImportConfiguration,
                     RecurringTransaction, Split, Transaction)

admin.site.register(ImportConfiguration)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(RecurringTransaction)
class RecurringTransactionAdmin(admin.ModelAdmin):
    search_fields = ['title']
    list_display = ('title', 'recurrence', 'date', 'amount')
    list_filter = ('recurrence',)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('account_type',)
    actions = ['merge_accounts']
    search_fields = ['name']

    def merge_accounts(self, request, queryset):
        accounts = list(queryset)
        if len(accounts) < 2:
            self.message_user(request,
                              _('You need to select more than one account to merge them.'),
                              messages.ERROR)
            return
        for account in accounts:
            failure = False
            if account.account_type != Account.FOREIGN:
                self.message_user(request, _(
                    'You can only merge foreign accounts, "{}" isn\'t.'.format(account.name)))
                failure = True
        if failure:
            return
        base = accounts.pop()
        for account in accounts:
            # update splits
            Split.objects.filter(account_id=account.id).update(account_id=base.id)
            Split.objects.filter(opposing_account_id=account.id).update(opposing_account_id=base.id)
            # update recurrences
            RecurringTransaction.objects.filter(src_id=account.id).update(src_id=base.id)
            RecurringTransaction.objects.filter(dst_id=account.id).update(dst_id=base.id)
            account.delete()
        if len(accounts) == 1:
            self.message_user(request, format_html(
                _('Merged one account into <a href={}>{}</a>.'),
                reverse('admin:silverstrike_account_change', args=[base.id]),
                base))
        else:
            self.message_user(request, format_html(
                _('Merged {} accounts into <a href={}>{}</a>.'),
                len(accounts),
                reverse('admin:silverstrike_account_change', args=[base.id]),
                base))


class SplitInline(admin.TabularInline):
    model = Split


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    inlines = [SplitInline]
    date_hierarchy = 'date'
    search_fields = ['title', 'notes', 'splits__title']
