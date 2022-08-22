from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from formtools.wizard.views import SessionWizardView, NamedUrlSessionWizardView
from django.urls import reverse

from .models import Post
from .forms import PostForm
# Create your views here.
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts':posts})


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    return render(request, 'blog/post_detail.html', {'post': post})

def post_new(request):
    if request.method=="POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('blog:post_detail', pk= post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form':form})

def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('blog:post_detail', pk= post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form':form}) 

# Create your views here.
def show_message_form_condition(wizard):
    # try to get the cleaned data of step 1
    cleaned_data = wizard.get_cleaned_data_for_step('contactdata') or {}
    # check if the field ``leave_message`` was checked.
    return cleaned_data.get('leave_message', True)

class ContactWizard(NamedUrlSessionWizardView):
    def get_step_url(self, step):
        return reverse(self.url_name, kwargs={'step':step})

    def done(self, form_list, **kwargs):
        return render(self.request, 'blog/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
        })
