from django import forms
from django.forms import ValidationError

class NonsiderealTargetVisibilityForm(forms.Form):
    start_time = forms.DateTimeField(required=True, label='Start Time', widget=forms.TextInput(attrs={'type': 'date'}))
    end_time = forms.DateTimeField(required=True, label='End Time', widget=forms.TextInput(attrs={'type': 'date'}))
    airmass = forms.DecimalField(required=False, label='Maximum Airmass')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if end_time < start_time:
            raise forms.ValidationError('Start time must be before end time')
