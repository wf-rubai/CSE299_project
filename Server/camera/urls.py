from django.urls import path

from . import views


urlpatterns = [
    path('view/', views.view_camera, name='view_camera'),
]
