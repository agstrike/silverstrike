from rest_framework import generics, serializers, viewsets, permissions
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from silverstrike.models import Account, Category, Transaction, Split
from silverstrike.rest.serializers import AccountSerializer, CategorySerializer, SplitSerializer, TransactionSerializer
from silverstrike.rest.permissions import ProtectSystemAccount


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (ProtectSystemAccount,)
    filter_fields = ('account_type',)

    @detail_route()
    def transactions(self, request, pk=None):
        account = self.get_object()
        transactions = Split.objects.filter(account=account)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = SplitSerializer(page, many=True, context={'request': request})
            return Response(serializer.data)
        serializer = SplitSerializer(transactions, many=True, context={'request': request})
        return Response(serializer.data)

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_fields = ('date', 'transaction_type')


class SplitViewSet(viewsets.ModelViewSet):
    queryset = Split.objects.all()
    serializer_class = SplitSerializer
    filter_fields = ('date', 'account', 'opposing_account', 'category', 'transaction__date', 'amount')


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
