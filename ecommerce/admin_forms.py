# admin_forms.py
from django import forms
from ckeditor.widgets import CKEditorWidget
from dashboard.models import Product

class ProductAdminForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorWidget())  # CKEditor widget here

    class Meta:
        model = Product
        fields = '__all__'
