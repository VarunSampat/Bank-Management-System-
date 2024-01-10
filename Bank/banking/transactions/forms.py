import datetime

from django import forms
from django.conf import settings
from django import forms
from accounts.models import UserBankAccount
from .models import Transaction


class TransactionForm(forms.ModelForm):

    class Meta:
        model = Transaction
        fields = [
            'amount',
            'transaction_type'
        ]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)

        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()


class DepositForm(TransactionForm):

    def clean_amount(self):
        min_deposit_amount = settings.MINIMUM_DEPOSIT_AMOUNT
        amount = self.cleaned_data.get('amount')

        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} ₹'
            )

        return amount


class WithdrawForm(TransactionForm):

    def clean_amount(self):
        account = self.account
        min_withdraw_amount = settings.MINIMUM_WITHDRAWAL_AMOUNT
        max_withdraw_amount = (
            account.account_type.maximum_withdrawal_amount
        )
        balance = account.balance

        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} ₹'
            )

        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} ₹'
            )

        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} ₹ in your account. '
                'You can not withdraw more than your account balance'
            )

        return amount


class TransactionDateRangeForm(forms.Form):
    daterange = forms.CharField(required=False)

    def clean_daterange(self):
        daterange = self.cleaned_data.get("daterange")
        print(daterange)

        try:
            daterange = daterange.split(' - ')
            print(daterange)
            if len(daterange) == 2:
                for date in daterange:
                    datetime.datetime.strptime(date, '%Y-%m-%d')
                return daterange
            else:
                raise forms.ValidationError("Please select a date range.")
        except (ValueError, AttributeError):
            raise forms.ValidationError("Invalid date range")

class TransferForm(forms.Form):
    sender_account = forms.ModelChoiceField(queryset=UserBankAccount.objects.all(), label='Sender Account')
    receiver_account = forms.ModelChoiceField(queryset=UserBankAccount.objects.all(), label='Receiver Account')
    amount = forms.DecimalField(min_value=0, max_digits=12, decimal_places=2)

    def clean(self):
        cleaned_data = super().clean()
        sender_account = cleaned_data.get('sender_account')
        receiver_account = cleaned_data.get('receiver_account')

        if sender_account == receiver_account:
            raise forms.ValidationError("Sender and receiver accounts cannot be the same.")

        return cleaned_data
