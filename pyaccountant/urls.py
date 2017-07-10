from django.conf.urls import url

from . import api, views


urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),

    url(r'^transactions/$', views.TransactionIndex.as_view(), name='transactions'),
    url(r'^transactions/(?P<pk>\d+)$',
        views.TransactionIndex.as_view(), name='account_transactions'),
    url(r'^transactions/create/transfer$',
        views.TransferCreate.as_view(), name='transfer_new'),
    url(r'^transactions/create/withdraw$',
        views.WithdrawCreate.as_view(), name='withdraw_new'),
    url(r'^transactions/create/deposit$',
        views.DepositCreate.as_view(), name='deposit_new'),
    url(r'^transactions/edit/(?P<pk>\d+)$',
        views.TransactionUpdate.as_view(), name='transaction_edit'),

    url(r'^accounts/new$', views.AccountCreate.as_view(), name='account_new'),
    url(r'^accounts/personal$',
        views.AccountIndex.as_view(account_type='personal'), name='personal_accounts'),
    url(r'^accounts/expense$',
        views.AccountIndex.as_view(account_type='expense'), name='expense_accounts'),
    url(r'^accounts/revenue$',
        views.AccountIndex.as_view(account_type='revenue'), name='revenue_accounts'),
    url(r'^accounts/update/(?P<pk>\d+)$', views.AccountUpdate.as_view(), name='account_update'),

    url(r'^api/accounts/(?P<account_type>\w+)$', api.get_accounts, name='api_accounts')
]
