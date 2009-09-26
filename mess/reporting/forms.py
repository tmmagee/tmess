import datetime

from django import forms
from mess.autocomplete import AutoCompleteWidget
from mess.accounting import models as a_models
from mess.membership import models as m_models

LIST_OBJECT_CHOICES = (
    ('Accounts', 'Accounts'),
    ('Members', 'Members'),
    ('Tasks', 'Tasks'),
)

class ListFilterForm(forms.Form):
    # this really is required, but not if the form wasn't submitted...
    object = forms.ChoiceField(required=False, choices=LIST_OBJECT_CHOICES)
    include_inactive = forms.BooleanField(required=False)
    filter = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':4, 'wrap':'off'}))
    order_by = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':2, 'wrap':'off'}))
    output = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':6, 'wrap':'off'}))

class TransactionFilterForm(forms.Form):
    start = forms.DateTimeField(initial=datetime.date.today())
    end = forms.DateTimeField(initial=datetime.date.today()+datetime.timedelta(1))
    list_each = forms.BooleanField(required=False)
    type = forms.ChoiceField(required=False, choices=
           (('','All'),) + a_models.PURCHASE_CHOICES + a_models.PAYMENT_CHOICES)
    note = forms.CharField(required=False)

class HoursBalanceChangesFilterForm(forms.Form):
    start = forms.DateField(required=False, 
        initial=datetime.date.today()-datetime.timedelta(7))
    end = forms.DateField(required=False, 
        initial=datetime.date.today()+datetime.timedelta(1))
    account = forms.ModelChoiceField(m_models.Account.objects.all(),
        widget=AutoCompleteWidget('account_spiffy',
            view_name='membership-autocomplete', canroundtrip=True),
        required=False)
