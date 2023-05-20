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