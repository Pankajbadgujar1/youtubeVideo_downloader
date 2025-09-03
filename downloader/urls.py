from django.urls import path
from . import views

app_name = 'downloader'

urlpatterns = [
    path('', views.index, name='index'),
    path('get_streams/', views.get_streams, name='get_streams'),
    path('download/', views.download_video, name='download'),
]