from django.shortcuts import render
from django.views import generic
from django.http import HttpResponse
from django.core.paginator import Paginator

from .models import NewsArticles
# Create your views here.

def news_home(request):
    news_list = NewsArticles.objects.all().order_by('-pub_date')
    news_page = Paginator(news_list, 25) # Show 25 list per page.
    news_page_number = request.GET.get('page')
    news_page_obj = news_page.get_page(news_page_number)    #return HttpResponse("I am good")

    context = {
        'news_page_obj': news_page_obj,
    }
    return render(request, 'geodeticnews/homepage.html', context)


class NewsDetailView(generic.DetailView):
    model = NewsArticles