from django.conf.urls import url

from . import api, views
from .models import Account


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),

    url(r'^transactions/transfer/create$',
        views.TransferCreate.as_view(), name='transfer_new'),
    url(r'^transactions/withdraw/create$',
        views.WithdrawCreate.as_view(), name='withdraw_new'),
    url(r'^transactions/deposit/create$',
        views.DepositCreate.as_view(), name='deposit_new'),

    url(r'^transactions/edit/(?P<pk>\d+)$',
        views.TransferUpdate.as_view(), name='transaction_update'),

    url(r'^categories$', views.CategoryIndex.as_view(), name='categories'),

    url(r'^accounts/$', views.TransactionIndex.as_view(), name='accounts'),
    url(r'^accounts/(?P<pk>\d+)$',
        views.TransactionIndex.as_view(), name='account_transactions'),
    url(r'^accounts/new$', views.AccountCreate.as_view(), name='account_new'),
    url(r'^accounts/personal$',
        views.AccountIndex.as_view(account_type=Account.PERSONAL), name='personal_accounts'),
    url(r'^accounts/expense$',
        views.AccountIndex.as_view(account_type=Account.EXPENSE), name='expense_accounts'),
    url(r'^accounts/revenue$',
        views.AccountIndex.as_view(account_type=Account.REVENUE), name='revenue_accounts'),
    url(r'^accounts/update/(?P<pk>\d+)$', views.AccountUpdate.as_view(), name='account_update'),

    url(r'^api/accounts/(?P<account_type>\w+)$', api.get_accounts, name='api_accounts')
]
