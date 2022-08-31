from django.contrib import admin

# Import models here
from .models import Post

# Register your models here.
admin.site.register(Post)