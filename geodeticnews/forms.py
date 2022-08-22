from django import forms


# insert your forms
from .models import NewsArticles

class NewsArticleForm(forms.ModelForm):
    class Meta:
        model = NewsArticles
        fields = "__all__"