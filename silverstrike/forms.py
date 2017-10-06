from datetime import date
from itertools import groupby

from django import forms
from django.forms.models import ModelChoiceField, ModelChoiceIterator, ModelMultipleChoiceField
from django.utils.translation import ugettext as _

from .models import (Account, Category, ImportConfiguration, ImportFile,
                     RecurringTransaction, Split, Transaction)


class ImportUploadForm(forms.ModelForm):
    class Meta:
        model = ImportFile
        fields = ['file']
    configuration = forms.ModelChoiceField(queryset=ImportConfiguration.objects.all(),
                                           required=False)


class AccountCreateForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['name', 'initial_balance', 'active', 'show_on_dashboard']

    initial_balance = forms.DecimalField(max_digits=10, decimal_places=2, initial=0)

    def save(self, commit=True):
        account = super(AccountCreateForm, self).save(commit)
        if self.cleaned_data['initial_balance']:
            account.set_initial_balance(self.cleaned_data['initial_balance'])
        return account


class CSVDefinitionForm(forms.Form):
    field_type = forms.ChoiceField(choices=ImportConfiguration.FIELD_TYPES)


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'source_account', 'destination_account',
                  'amount', 'date', 'category', 'notes']

    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    source_account = forms.ModelChoiceField(queryset=Account.objects.filter(
        account_type=Account.PERSONAL))
    destination_account = forms.ModelChoiceField(queryset=Account.objects.filter(
        account_type=Account.PERSONAL))
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)

    def save(self, commit=True):
        transaction = super().save(commit)
        src = self.cleaned_data['source_account']
        dst = self.cleaned_data['destination_account']
        amount = self.cleaned_data['amount']
        Split.objects.update_or_create(transaction=transaction, amount__lt=0,
                                       defaults={'amount': -amount, 'account': src,
                                                 'opposing_account': dst, 'date': transaction.date,
                                                 'title': transaction.title,
                                                 'category': self.cleaned_data['category']})
        Split.objects.update_or_create(transaction=transaction, amount__gt=0,
                                       defaults={'amount': amount, 'account': dst,
                                                 'opposing_account': src, 'date': transaction.date,
                                                 'title': transaction.title,
                                                 'category': self.cleaned_data['category']})
        return transaction

    def clean(self):
        super().clean()
        self.instance.transaction_type = Transaction.TRANSFER
        if self.cleaned_data['source_account'] == self.cleaned_data['destination_account']:
            error = 'source and destination account have to be different'
            self.add_error('destination_account', error)
            self.add_error('source_account', error)


class WithdrawForm(TransferForm):
    destination_account = forms.CharField(max_length=64, label=_('Debitor'),
                                          widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def save(self, commit=True):
        account, _ = Account.objects.get_or_create(name=self.cleaned_data['destination_account'],
                                                   account_type=Account.EXPENSE)
        self.cleaned_data['destination_account'] = account
        return super().save(commit)

    def clean(self):
        super().clean()
        self.instance.transaction_type = Transaction.WITHDRAW


class DepositForm(TransferForm):
    source_account = forms.CharField(max_length=64, label=_('Creditor'),
                                     widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def save(self, commit=True):
        account, _ = Account.objects.get_or_create(name=self.cleaned_data['source_account'],
                                                   account_type=Account.REVENUE)
        self.cleaned_data['source_account'] = account
        return super().save(commit)

    def clean(self):
        super().clean()
        self.instance.transaction_type = Transaction.DEPOSIT


class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ['title', 'transaction_type', 'date', 'amount',
                  'src', 'dst', 'category', 'recurrence']

    src = forms.CharField(max_length=64, label=_('Source Account'),
                          widget=forms.TextInput(attrs={'autocomplete': 'off'}))
    dst = forms.CharField(max_length=64, label=_('Destination Account'),
                          widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 0:
            raise forms.ValidationError(_('Amount has to be positive'))
        return amount

    def clean_date(self):
        recurrence_date = self.cleaned_data['date']
        if recurrence_date < date.today():
            raise forms.ValidationError(_("Date can't be in the past"))
        return recurrence_date

    def clean(self):
        if self.cleaned_data['transaction_type'] == Transaction.TRANSFER:
            src_type = dst_type = Account.PERSONAL
        elif self.cleaned_data['transaction_type'] == Transaction.WITHDRAW:
            src_type = Account.PERSONAL
            dst_type = Account.EXPENSE
        else:
            src_type = Account.REVENUE
            dst_type = Account.PERSONAL
        src, _ = Account.objects.get_or_create(name=self.cleaned_data['src'],
                                               account_type=src_type)
        self.cleaned_data['src'] = src
        dst, _ = Account.objects.get_or_create(name=self.cleaned_data['dst'],
                                               account_type=dst_type)
        self.cleaned_data['dst'] = dst


class ReconcilationForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'current_balance', 'notes']

    current_balance = forms.DecimalField(max_digits=10, decimal_places=2, required=True)

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super(ReconcilationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        transaction = super().save(False)
        transaction.transaction_type = Transaction.SYSTEM
        transaction.save()
        src = Account.objects.get(account_type=Account.SYSTEM).pk
        dst = Account.objects.get(pk=self.account)
        balance = self.cleaned_data['current_balance']
        amount = balance - dst.balance
        Split.objects.create(transaction=transaction, amount=-amount,
                             account_id=src, opposing_account=dst, title=transaction.title)
        Split.objects.create(transaction=transaction, amount=amount,
                             account=dst, opposing_account_id=src, title=transaction.title)
        return transaction

    def clean(self):
        super().clean()
        if self.cleaned_data['current_balance'] == Account.objects.get(pk=self.account).balance:
            self.add_error('current_balance', 'You provided the same balance!')


class Grouped(object):
    def __init__(self, queryset, group_by_field,
                 group_label=None, *args, **kwargs):
        """
        ``group_by_field`` is the name of a field on the model to use as
                           an optgroup.
        ``group_label`` is a function to return a label for each optgroup.
        """
        queryset = queryset.order_by(group_by_field)
        super(Grouped, self).__init__(queryset, *args, **kwargs)
        self.group_by_field = group_by_field
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)


class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        queryset = self.queryset.all()
        if not queryset._prefetch_related_lookups:
            queryset = queryset.iterator()
        for group, choices in groupby(self.queryset.all(),
                                      key=lambda row: getattr(row, self.field.group_by_field)):
            if self.field.group_label(group):
                yield (
                    self.field.group_label(group),
                    [self.choice(ch) for ch in choices]
                )


class GroupedModelChoiceField(Grouped, ModelChoiceField):
    choices = property(Grouped._get_choices, ModelChoiceField._set_choices)


class GroupedModelMultiChoiceField(Grouped, ModelMultipleChoiceField):
    choices = property(Grouped._get_choices, ModelMultipleChoiceField._set_choices)


class SplitForm(forms.ModelForm):
    class Meta:
        model = Split
        exclude = ['transaction', 'id']
    account = GroupedModelChoiceField(queryset=Account.objects.exclude(account_type=Account.SYSTEM),
                                      group_by_field='account_type',
                                      group_label=lambda type: Account.ACCOUNT_TYPES[type - 1][1])
    opposing_account = GroupedModelChoiceField(
        queryset=Account.objects.exclude(account_type=Account.SYSTEM),
        group_by_field='account_type',
        group_label=lambda type: Account.ACCOUNT_TYPES[type - 1][1])


TransactionFormSet = forms.models.inlineformset_factory(
    Transaction, Split, form=SplitForm, extra=1
    )
