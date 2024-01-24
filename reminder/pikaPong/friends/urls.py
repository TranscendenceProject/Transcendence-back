from django.urls import path
from . import views

urlpatterns = [
    path('add', views.add_friend_to_user_profile, name='add_friend_to_user_profile'),
    path('list', views.get_friends_of_user_profile, name='get_friends_of_user_profile'),
    path('delete', views.remove_friend_from_user_profile, name='remove_friend_from_user_profile'),
]
