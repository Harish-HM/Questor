from django.urls import path
from . import views

urlpatterns = [
    path('', views.extract_keywords_view, name='extract_keywords'),
    path('fetch-links/', views.fetch_links_view, name='fetch_links'),
    path('extract-emails/', views.extract_emails_view, name='extract_emails'),
]


