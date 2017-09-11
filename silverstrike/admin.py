from django.contrib import admin

from .models import (Account, Category, ImportConfiguration,
                     Journal, RecurringTransaction, Split)

admin.site.register(Category)
admin.site.register(ImportConfiguration)
admin.site.register(RecurringTransaction)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('account_type',)


class SplitInline(admin.TabularInline):
    model = Split

    def get_extra(self, request, obj=None, **kwargs):
        if obj:
            return 0
        else:
            return 4


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    inlines = [SplitInline]
    date_hierarchy = 'date'
    search_fields = ['title', 'notes', 'split__description']
