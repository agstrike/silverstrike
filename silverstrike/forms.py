from django import forms
from django.utils.translation import ugettext as _

from .models import (Account, Budget, Category, ImportConfiguration, ImportFile,
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


class BudgetForm(forms.Form):
    budget_id = forms.IntegerField()
    category_id = forms.IntegerField()
    category_name = forms.CharField(max_length=64)
    spent = forms.CharField(max_length=32)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    left = forms.CharField(max_length=32)
    month = forms.DateField()

    def save(self):
        if self.cleaned_data['budget_id'] == -1:
            if self.cleaned_data['amount'] != 0:
                # new budget
                Budget.objects.create(
                    category_id=self.cleaned_data['category_id'],
                    month=self.cleaned_data['month'],
                    amount=self.cleaned_data['amount'])
        elif self.cleaned_data['amount'] != 0:
            Budget.objects.update_or_create(id=self.cleaned_data['budget_id'], defaults={
                'amount': self.cleaned_data['amount']
            })
        else:
            Budget.objects.get(id=self.cleaned_data['budget_id']).delete()


BudgetFormSet = forms.formset_factory(BudgetForm, extra=0)


class CSVDefinitionForm(forms.Form):
    field_type = forms.ChoiceField(choices=ImportConfiguration.FIELD_TYPES)


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'source_account', 'destination_account',
                  'amount', 'date', 'value_date', 'category', 'notes']

    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    category = forms.ModelChoiceField(
        queryset=Category.objects.exclude(active=False).order_by('name'), required=False)
    value_date = forms.DateField(required=False)

    source_account = forms.ModelChoiceField(queryset=Account.objects.filter(
        account_type=Account.PERSONAL, active=True))
    destination_account = forms.ModelChoiceField(queryset=Account.objects.filter(
        account_type=Account.PERSONAL, active=True))

    def save(self, commit=True):
        transaction = super().save(commit)
        src = self.cleaned_data['source_account']
        dst = self.cleaned_data['destination_account']
        amount = self.cleaned_data['amount']
        value_date = self.cleaned_data.get('value_date') or transaction.date
        Split.objects.update_or_create(transaction=transaction, amount__lt=0,
                                       defaults={'amount': -amount, 'account': src,
                                                 'opposing_account': dst, 'date': value_date,
                                                 'title': transaction.title,
                                                 'category': self.cleaned_data['category']})
        Split.objects.update_or_create(transaction=transaction, amount__gt=0,
                                       defaults={'amount': amount, 'account': dst,
                                                 'opposing_account': src, 'date': value_date,
                                                 'title': transaction.title,
                                                 'category': self.cleaned_data['category']})
        return transaction


class TransferForm(TransactionForm):
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


class WithdrawForm(TransactionForm):
    destination_account = forms.CharField(max_length=64, label=_('Debitor'),
                                          widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def save(self, commit=True):
        account, _ = Account.objects.get_or_create(name=self.cleaned_data['destination_account'],
                                                   account_type=Account.FOREIGN)
        self.cleaned_data['destination_account'] = account
        return super().save(commit)

    def clean(self):
        super().clean()
        self.instance.transaction_type = Transaction.WITHDRAW


class DepositForm(TransactionForm):
    source_account = forms.CharField(max_length=64, label=_('Creditor'),
                                     widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def save(self, commit=True):
        account, _ = Account.objects.get_or_create(name=self.cleaned_data['source_account'],
                                                   account_type=Account.FOREIGN)
        self.cleaned_data['source_account'] = account
        return super().save(commit)

    def clean(self):
        super().clean()
        self.instance.transaction_type = Transaction.DEPOSIT


class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = ['title', 'date', 'amount',
                  'src', 'dst', 'category', 'recurrence']

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 0:
            raise forms.ValidationError(_('Amount has to be positive'))
        return amount

    def clean(self):
        super(RecurringTransactionForm, self).clean()
        src = self.cleaned_data['src']
        dst = self.cleaned_data['dst']
        if src.account_type == Account.PERSONAL:
            if dst.account_type == Account.PERSONAL:
                self.transaction_type = Transaction.TRANSFER
            else:
                self.transaction_type = Transaction.WITHDRAW
        elif dst.account_type == Account.PERSONAL:
            self.transaction_type = Transaction.DEPOSIT
        else:
            raise forms.ValidationError(
                _('You are trying to create a transaction between two foreign accounts'))

    def save(self, commit=False):
        recurrence = super(RecurringTransactionForm, self).save(commit=False)
        recurrence.transaction_type = self.transaction_type
        recurrence.save()
        return recurrence


class ReconcilationForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'balance', 'notes']

    balance = forms.DecimalField(max_digits=10, decimal_places=2, required=True,
                                 label=_('Actual balance'))

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super(ReconcilationForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        transaction = super().save(False)
        transaction.transaction_type = Transaction.SYSTEM
        transaction.save()
        src = Account.objects.get(account_type=Account.SYSTEM).pk
        dst = Account.objects.get(pk=self.account)
        balance = self.cleaned_data['balance']
        amount = balance - dst.balance
        Split.objects.create(transaction=transaction, amount=-amount,
                             account_id=src, opposing_account=dst, title=transaction.title)
        Split.objects.create(transaction=transaction, amount=amount,
                             account=dst, opposing_account_id=src, title=transaction.title)
        return transaction

    def clean(self):
        super().clean()
        if self.cleaned_data['balance'] == Account.objects.get(pk=self.account).balance:
            self.add_error('balance', 'You provided the same balance!')


class SplitForm(forms.ModelForm):
    class Meta:
        model = Split
        fields = ['title', 'account', 'opposing_account', 'date', 'amount', 'category']
    account = forms.ModelChoiceField(queryset=Account.objects.exclude(
        account_type=Account.SYSTEM))
    opposing_account = forms.ModelChoiceField(queryset=Account.objects.exclude(
        account_type=Account.SYSTEM))


TransactionFormSet = forms.models.inlineformset_factory(
    Transaction, Split, form=SplitForm, extra=1
    )


class ExportForm(forms.Form):
    start = forms.DateField()
    end = forms.DateField()
    accounts = forms.ModelMultipleChoiceField(
        queryset=Account.objects.filter(account_type=Account.PERSONAL))


CategoryAssignFormset = forms.modelformset_factory(Split, fields=('category',), extra=0)
