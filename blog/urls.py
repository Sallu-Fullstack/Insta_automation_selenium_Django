from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='home'),
    path('schedule_posts/', views.schedule_posts, name='schedule_posts'),
    path('user_login/', views.user_login, name='user_login'),
    path('user_code/', views.user_code, name='user_code'),
    path('delete_cookies/', views.delete_cookies, name='delete_cookies'),
    path('post_insta/', views.post_insta, name='post_insta'),
    path('explore_scheduled/', views.explore_scheduled, name='explore_scheduled'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('remove_unfollowers/', views.remove_unfollowers, name='remove_unfollowers'),
    path('story_viewer/', views.story_viewer, name='story_viewer'),
    path('follower_interactions/', views.follower_interactions, name='follower_interactions'),
    path('explore_scheduled_users/', views.explore_scheduled_users, name='explore_scheduled_users'),
    path('share_to_followers/', views.share_to_followers, name='share_to_followers'),
    path('download_followers/', views.download_followers, name='download_followers'),
    path('multiple_likes/', views.multiple_likes, name='multiple_likes')
]




# urlpatterns = [
#     path('', views.homepage, name='home'),
#     # path('login/', views.user_login, name='user_login'),
#     # path('post_media/', views.post_media, name='post_media'),
#     path('schedule_posts/', views.schedule_posts, name='schedule_posts')
#     # path('delete_session/', views.delete_session_file, name='delete_session'),
#     # path('share_post/', views.share_post_with_followers, name='share_post'),
#     # path('delete_media/', views.delete_media, name='delete_media'),
#     # path('retrieve_followers/', views.retrieve_followers, name='retrieve_followers'),
#     # Add other URLs as needed
# ]
