from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.manage_clubs, name='manage_clubs'),
    path('<int:pk>/', views.club_detail, name='club_detail'),
    path('create/', views.create_club, name='create_club'),
    path('<int:pk>/edit/', views.edit_club, name='edit_club'),
    path('<int:pk>/delete/', views.delete_club, name='delete_club'),
    path('delete/', views.delete_clubs, name='delete_clubs'),
    # Position management
    path('<int:pk>/positions/', views.manage_club_positions, name='manage_positions'),
    path('<int:pk>/positions/add/', views.add_club_position, name='add_position'),
    path('<int:pk>/positions/<int:position_pk>/edit/', views.edit_club_position, name='edit_position'),
    path('<int:pk>/positions/<int:position_pk>/delete/', views.delete_club_position, name='delete_position'),
    path('<int:pk>/positions/update-order/', views.update_position_order, name='update_position_order'),
    # Post management
    path('<int:pk>/posts/', views.manage_club_posts, name='manage_posts'),
    path('<int:pk>/posts/create/', views.create_club_post, name='create_post'),
    path('<int:pk>/posts/<int:post_pk>/edit/', views.edit_club_post, name='edit_post'),
    path('<int:pk>/posts/<int:post_pk>/delete/', views.delete_club_post, name='delete_post'),
    # Allowed email management (for conveners)
    path('<int:pk>/allowed-emails/', views.manage_club_allowed_emails, name='manage_allowed_emails'),
    path('<int:pk>/allowed-emails/create/', views.create_club_allowed_email, name='create_allowed_email'),
    path('<int:pk>/allowed-emails/<int:email_pk>/delete/', views.delete_club_allowed_email, name='delete_allowed_email'),
]

