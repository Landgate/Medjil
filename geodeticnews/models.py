from django.db import models
from django.urls import reverse
from accounts.models import CustomUser
# Create your models here.
class NewsArticles(models.Model):
	news_category = (
				(None, '--- Select Type ---'),
				# ('edm_lab', 'EDM Calibration Laboratory'),
				('breaking','Breaking News'),
				('innovation', 'Innovation'),
				('discovery','Discovery'), 
				('methods', 'Methods'),
				('research','Research Articles'), 
				('news', 'News'),
				('history', 'History'), 
				('story', 'Story')
				)
	category = models.CharField(max_length=20,
								choices=news_category, 
								null=True,
							)
	headline = models.CharField(max_length=200)
	content = models.TextField()
	img = models.ImageField('Article Image')
	author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	pub_date = models.DateTimeField(auto_now_add=True, null=True)
	mod_date = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.headline
	
	def get_absolute_url(self):
		"""Returns the URl to access the detail record of this news"""
		return reverse('geodeticnews:news-detail', args=[str(self.id)])