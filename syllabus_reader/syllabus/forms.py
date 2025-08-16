from django import forms
from .models import Provider, Curriculum, Syllabus, Unit

class ProviderForm(forms.ModelForm):
    class Meta:
        model = Provider
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CurriculumForm(forms.ModelForm):
    class Meta:
        model = Curriculum
        fields = ['provider', 'title', 'description', 'start_date', 'end_date']
        widgets = {
            'provider': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class SyllabusForm(forms.ModelForm):
    class Meta:
        model = Syllabus
        fields = ['curriculum', 'name']
        widgets = {
            'curriculum': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['syllabus', 'title', 'description', 'ai_game']
        widgets = {
            'syllabus': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'ai_game': forms.Select(attrs={'class': 'form-select'}),
        }