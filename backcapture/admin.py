'''

   © 2023 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

'''
from django.contrib import admin
from .models import * 
from accounts.admin import admin_site

# Register your models here.
@admin.register(Backcapture_History, site=admin_site)
class Backcapture_HistoryeAdmin(admin.ModelAdmin):
    fields = ['user']

try:
    from accounts.sites import medjil_super_site    
    
    @admin.register(Backcapture_History, site=medjil_super_site)
    class Backcapture_HistoryAdmin(admin.ModelAdmin):
        fields = ['user']
except:
    pass