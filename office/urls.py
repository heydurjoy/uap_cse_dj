from django.urls import path
from . import views

app_name = 'office'

urlpatterns = [
    path('posts/', views.post_list, name='post_list'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('posts/manage/', views.manage_posts, name='manage_posts'),
    path('posts/create/', views.create_post, name='create_post'),
    path('posts/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('posts/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('posts/delete/', views.delete_posts, name='delete_posts'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
]

