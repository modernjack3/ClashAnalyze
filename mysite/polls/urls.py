from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:player_name>/plot/', views.plot, name='plot'),
]