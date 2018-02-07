from django.contrib import admin

# Register your models here.
from .models import Faq, Tutorial
admin.site.register(Faq)
admin.site.register(Tutorial)
