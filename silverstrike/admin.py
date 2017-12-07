from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext as _


from .models import (Account, Category, ImportConfiguration,
                     RecurringTransaction, Split, Transaction)

admin.site.register(Category)
admin.site.register(ImportConfiguration)
admin.site.register(RecurringTransaction)


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
        base = accounts.pop()
        for account in accounts:
            Split.objects.filter(account_id=account.id).update(account_id=base.id)
            Split.objects.filter(opposing_account_id=account.id).update(opposing_account_id=base.id)
            account.delete()
        if len(accounts) == 1:
            message = _('1 account')
        else:
            message = _('{} accounts' % len(accounts))
        self.message_user(request, format_html(
            _('Merged {} into <a href={}>{}</a>.'),
            message,
            reverse('admin:silverstrike_account_change', args=[base.id]),
            base))


class SplitInline(admin.TabularInline):
    model = Split

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return 0
        else:
            return 4


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    inlines = [SplitInline]
    date_hierarchy = 'date'
    search_fields = ['title', 'notes', 'splits__title']
