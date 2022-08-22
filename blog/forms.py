from django import forms

from .models import Post

# Prepare forms
class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title','text',)

class ContactForm1(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.EmailField()
    leave_message = forms.BooleanField(required=False)

class ContactForm2(forms.Form):
    message = forms.CharField(widget=forms.Textarea)