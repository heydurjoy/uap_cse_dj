from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/<int:pk>/', views.faculty_detail, name='faculty_detail'),
    path('officers/', views.officer_list, name='officer_list'),
    path('officers/<int:pk>/', views.officer_detail, name='officer_detail'),
    path('club-members/<int:pk>/', views.club_member_detail, name='club_member_detail'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('manage-permissions/', views.manage_user_permissions_list, name='manage_user_permissions_list'),
    path('manage-permissions/self/', views.manage_user_permissions, {'user_id': 'self'}, name='manage_own_permissions'),
    path('manage-permissions/<int:user_id>/', views.manage_user_permissions, name='manage_user_permissions'),
    path('allowed-emails/create/', views.create_allowed_email, name='create_allowed_email'),
    path('allowed-emails/<int:pk>/edit/', views.edit_allowed_email, name='edit_allowed_email'),
    path('allowed-emails/bulk-delete/', views.bulk_delete_allowed_emails, name='bulk_delete_allowed_emails'),
    # Faculty management (power users only)
    path('manage-faculty/', views.manage_faculty, name='manage_faculty'),
    path('manage-faculty/create/', views.create_faculty, name='create_faculty'),
    path('manage-faculty/<int:pk>/edit/', views.edit_faculty, name='edit_faculty'),
    path('manage-faculty/update-order/', views.update_faculty_order, name='update_faculty_order'),
    path('manage-faculty/bulk-delete/', views.bulk_delete_faculty, name='bulk_delete_faculty'),
]

