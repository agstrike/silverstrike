from django import forms
from django.utils.translation import ugettext as _

from .models import Account, InternalAccountType, Transaction, TransactionJournal


class TransferForm(forms.ModelForm):
    class Meta:
        model = TransactionJournal
        fields = ['title', 'source_account', 'destination_account', 'amount', 'date', 'notes']

    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    source_account = forms.ModelChoiceField(queryset=Account.objects.filter(
        internal_type=InternalAccountType.personal.value))
    destination_account = forms.ModelChoiceField(queryset=Account.objects.filter(
        internal_type=InternalAccountType.personal.value))

    def save(self, commit=True):
        journal = super().save(commit)
        src = self.cleaned_data['source_account']
        dst = self.cleaned_data['destination_account']
        amount = self.cleaned_data['amount']
        Transaction.objects.update_or_create(journal=journal, amount__lt=0,
                                             defaults={'amount': -amount, 'account': src,
                                                       'opposing_account': dst})
        Transaction.objects.update_or_create(journal=journal, amount__gt=0,
                                             defaults={'amount': amount, 'account': dst,
                                                       'opposing_account': src})
        return journal

    def clean(self):
        super().clean()
        if self.cleaned_data['source_account'] == self.cleaned_data['destination_account']:
            error = 'source and destination account have to be different'
            self.add_error('destination_account', error)
            self.add_error('source_account', error)


class WithdrawForm(TransferForm):
    destination_account = forms.CharField(max_length=64, label=_('Debitor'),
                                          widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def save(self, commit=True):
        account, _ = Account.objects.get_or_create(name=self.cleaned_data['destination_account'],
                                                   active=True,
                                                   internal_type=InternalAccountType.expense.value)
        self.cleaned_data['destination_account'] = account
        return super().save(commit)


class DepositForm(TransferForm):
    source_account = forms.CharField(max_length=64, label=_('Creditor'),
                                     widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    def save(self, commit=True):
        account, _ = Account.objects.get_or_create(name=self.cleaned_data['source_account'],
                                                   active=True,
                                                   internal_type=InternalAccountType.revenue.value)
        self.cleaned_data['source_account'] = account
        return super().save(commit)
