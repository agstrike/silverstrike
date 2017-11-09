from rest_framework import serializers

from silverstrike.models import Account, Category, Split, Transaction


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'account_type', 'active', 'show_on_dashboard')

    def validate_account_type(self, value):
        if value == Account.SYSTEM:
            raise serializers.ValidationError("You can't create system accounts")
        return value


class SplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Split
        fields = ('id', 'title', 'date', 'account', 'opposing_account',
                  'amount', 'category', 'transaction')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'title', 'date', 'transaction_type', 'splits')

    splits = SplitSerializer(many=True)

    def create(self, validated_data):
        split_sum = sum([split['amount'] for split in validated_data['splits']])
        if split_sum != 0:
            raise serializers.ValidationError("The sum of splits does not balance")
        split_data = validated_data.pop('splits')
        transaction = Transaction.objects.create(**validated_data)

        for split in split_data:
            Split.objects.create(transaction=transaction, **split)
        return transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')
