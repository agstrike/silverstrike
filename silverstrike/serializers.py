from rest_framework import generics, serializers, viewsets

from silverstrike.models import Account, Category, Transaction, Split

class AccountSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'account_type', 'active', 'show_on_dashboard')

class TransactionSerializer(serializers.HyperlinkedModelSerializer):
    splits = serializers.HyperlinkedIdentityField(many=True, read_only=True, view_name='split-detail')

    class Meta:
        model = Transaction
        fields = ('id', 'title', 'date', 'transaction_type', 'splits')

class AccountList(viewsets.ModelViewSet):
    queryset = Account.objects.exclude(account_type=Account.SYSTEM)
    serializer_class = AccountSerializer
    filter_fields = ('account_type',)

class Transactions(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filter_fields = ('date', 'transaction_type')

class SplitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Split
        fields = ('id', 'title', 'date', 'account', 'opposing_account',
                  'amount', 'category', 'transaction')


class Splits(viewsets.ModelViewSet):
    queryset = Split.objects.all()
    serializer_class = SplitSerializer
    filter_fields = ('date', 'account', 'opposing_account', 'category', 'transaction__date', 'amount')


class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class Categories(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
