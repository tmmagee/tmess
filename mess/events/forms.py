from django import forms
from django.forms import ModelForm
from django.contrib.admin import widgets
from mess.events.models import Orientation, Location
from mess.membership import models as m_models
from mess.autocomplete import AutoCompleteWidget

class OrientationForm(ModelForm):
    class Meta:
        model = Orientation

    staff_contact = forms.ModelChoiceField(m_models.Member.objects.all(),
      widget=AutoCompleteWidget('member_spiffy',
        view_name='membership-autocomplete', 
        canroundtrip=True),
      required=False, 
      help_text='* = include inactive') 

    facilitator = forms.ModelChoiceField(m_models.Member.objects.all(),
      widget=AutoCompleteWidget('member_spiffy',
        view_name='membership-autocomplete', 
        canroundtrip=True),
      required=False, 
      help_text='* = include inactive') 

    cofacilitator = forms.ModelChoiceField(m_models.Member.objects.all(),
      widget=AutoCompleteWidget('member_spiffy',
        view_name='membership-autocomplete', 
        canroundtrip=True),
      required=False, 
      help_text='* = include inactive') 

    def  __init__(self, *args, **kwargs):
        super(OrientationForm, self).__init__(*args, **kwargs)
        self.fields["description"].required=False

class LocationForm(ModelForm):
    class Meta:
        model = Location

    def  __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
