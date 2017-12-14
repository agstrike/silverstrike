from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from silverstrike.models import Account, Category, RecurringTransaction, Split, Transaction
from silverstrike.rest.permissions import ProtectSystemAccount
from silverstrike.rest.serializers import (AccountSerializer, CategorySerializer,
                                           RecurringTransactionSerializer,
                                           SplitSerializer, TransactionSerializer)


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (ProtectSystemAccount,)

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


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class RecurringTransactionsViewset(viewsets.ModelViewSet):
    queryset = RecurringTransaction.objects.all()
    serializer_class = RecurringTransactionSerializer
