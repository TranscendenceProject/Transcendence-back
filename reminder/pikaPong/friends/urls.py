from django.urls import path
from . import views

urlpatterns = [
    path('add', views.add_friend_to_user_profile, name='add_friend_to_user_profile'),
]
