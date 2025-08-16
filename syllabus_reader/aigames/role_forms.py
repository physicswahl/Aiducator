from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserRoleForm(forms.ModelForm):
    """Form for managing user roles"""
    class Meta:
        model = UserProfile
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'})
        }

class BulkUserRoleForm(forms.Form):
    """Form for bulk updating user roles"""
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select users to update"
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Role to assign to selected users"
    )
