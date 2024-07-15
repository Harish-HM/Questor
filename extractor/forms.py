from django import forms
from .models import UploadedExcel

class ExcelUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedExcel
        fields = ['excel_file']

class CleanOptionsForm(forms.Form):
    column_name = forms.CharField(label='Column Name')

class KeywordUploadForm(forms.ModelForm):
    class Meta:
        model = UploadedExcel
        fields = ['excel_file']

class LinkOptionsForm(forms.Form):
    # num_links = forms.IntegerField(label="Number of Links", min_value=1, max_value=100)
    index_filter = forms.CharField(label="Enter Range (eg 1-10)", required=False)
class URLInputForm(forms.Form):
    single_url = forms.URLField(label='Enter a single URL')