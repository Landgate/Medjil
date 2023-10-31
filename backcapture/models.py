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
from django.db import models
from accounts.models import CustomUser

# Create your models here.
class Backcapture_History(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete = models.CASCADE)
    created_on = models.DateTimeField(
        auto_now_add=True, 
        null=True)
        
    def __str__(self):
        return self.user