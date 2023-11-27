from django import forms
from .models import AudioFile


class AudioFileForm(forms.ModelForm):
    class Meta:
        model = AudioFile
        fields = ["audio"]


class SummarizeTextForm(forms.Form):
    text_data = forms.FileField(allow_empty_file=False)
    # ... [rest of your form fields if any]