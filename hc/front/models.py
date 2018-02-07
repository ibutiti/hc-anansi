from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# The FAQs model
class Faq(models.Model):
    """
    This model operates the FAQ table and instance objects
    """
    question = models.CharField(max_length=150, blank=False)
    answer = models.TextField(max_length=1000, blank=False)

    def __str__(self):
        """
        Object string representation
        """
        return self.question
# The Tutorial model
class Tutorial(models.Model):
    """
    This model operates the FAQ table and instance objects
    """
    title = models.CharField(max_length=150, blank=False)
    content = models.TextField(max_length=2000, blank=True)
    video_link = models.CharField(max_length=150, blank=True)

    def __str__(self):
        """
        Object string representation
        """
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

    
class Blog_post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    published = models.DateTimeField(null=timezone.now)
    category = models.ForeignKey(Category, on_delete = models.CASCADE)
    user = models.ForeignKey(User, blank=True, null=True, on_delete = models.CASCADE)

    def __str__(self):
        return f"{self.title}"

class Comment(models.Model):
    comment = models.TextField()
    blog = models.ForeignKey(Blog_post, blank=True, null=True )
    user = models.ForeignKey(User, blank=True, null=True, on_delete = models.CASCADE)
    published = models.DateTimeField(null=timezone.now)


    def __str__(self):
        return f"{self.comment}"
