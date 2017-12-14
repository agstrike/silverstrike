from rest_framework import serializers

from silverstrike.models import Account, Category, RecurringTransaction, Split, Transaction


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', 'name', 'account_type', 'active', 'show_on_dashboard', 'last_modified')
        read_only_fields = ('last_modified',)

    def validate_account_type(self, value):
        if value == Account.SYSTEM:
            raise serializers.ValidationError("You can't create system accounts")
        return value


class SplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Split
        fields = ('id', 'title', 'date', 'account', 'opposing_account',
                  'amount', 'category', 'transaction', 'last_modified')
        read_only_fields = ('last_modified',)

    # needed so that the id is transfered for update actions
    id = serializers.IntegerField(required=False)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'title', 'date', 'transaction_type', 'splits', 'last_modified')
        read_only_fields = ('last_modified',)

    splits = SplitSerializer(many=True)

    def validate(self, data):
        split_sum = sum([split['amount'] for split in data['splits']])
        if split_sum != 0:
            raise serializers.ValidationError("The sum of splits does not balance")
        return data

    def create(self, validated_data):
        split_data = validated_data.pop('splits')
        transaction = Transaction.objects.create(**validated_data)

        for split in split_data:
            Split.objects.create(transaction=transaction, **split)
        return transaction

    def update(self, instance, validated_data):
        # update transaction
        instance.title = validated_data.get('title', instance.title)
        instance.date = validated_data.get('date', instance.date)
        instance.transaction_type = validated_data.get('transaction_type',
                                                       instance.transaction_type)
        instance.save()
        # update splits
        for split in validated_data.get('splits'):
            split_object = Split.objects.get(id=split.get('id'))

            split_object.title = split.get('title', split_object.title)
            split_object.date = split.get('date', split_object.date)
            split_object.account = split.get('account', split_object.account)
            split_object.opposing_account = split.get('opposing_account',
                                                      split_object.opposing_account)
            split_object.amount = split.get('amount', split_object.amount)
            split_object.category = split.get('category', split_object.category)
            split_object.save()
        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'active', 'last_modified')
        read_only_fields = ('last_modified',)


class RecurringTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTransaction
        fields = ('id', 'title', 'src', 'dst', 'amount', 'date',
                  'recurrence', 'category', 'transaction_type', 'last_modified')
        read_only_fields = ('last_modified',)
