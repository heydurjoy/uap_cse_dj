from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/<int:pk>/', views.faculty_detail, name='faculty_detail'),
    path('faculty/<int:pk>/cv/', views.serve_faculty_cv, name='serve_faculty_cv'),
    path('research/', views.departmental_research, name='departmental_research'),
    path('officers/', views.officer_list, name='officer_list'),
    path('officers/<int:pk>/', views.officer_detail, name='officer_detail'),
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/', views.staff_detail, name='staff_detail'),
    path('club-members/<int:pk>/', views.club_member_detail, name='club_member_detail'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('manage-permissions/', views.manage_user_permissions_list, name='manage_user_permissions_list'),
    path('manage-permissions/self/', views.manage_user_permissions, {'user_id': 'self'}, name='manage_own_permissions'),
    path('manage-permissions/<int:user_id>/', views.manage_user_permissions, name='manage_user_permissions'),
    # Permission Objects Management
    path('manage-permission-objects/', views.manage_permissions, name='manage_permissions'),
    path('manage-permission-objects/create/', views.create_permission, name='create_permission'),
    path('manage-permission-objects/<int:pk>/edit/', views.edit_permission, name='edit_permission'),
    path('manage-permission-objects/<int:pk>/delete/', views.delete_permission, name='delete_permission'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('allowed-emails/create/', views.create_allowed_email, name='create_allowed_email'),
    path('allowed-emails/<int:pk>/edit/', views.edit_allowed_email, name='edit_allowed_email'),
    path('allowed-emails/<int:email_id>/posts/', views.get_user_posts, name='get_user_posts'),
    path('allowed-emails/bulk-delete/', views.bulk_delete_allowed_emails, name='bulk_delete_allowed_emails'),
    # Faculty management (power users only)
    path('manage-faculty/', views.manage_faculty, name='manage_faculty'),
    path('manage-faculty/create/', views.create_faculty, name='create_faculty'),
    path('manage-faculty/<int:pk>/edit/', views.edit_faculty, name='edit_faculty'),
    path('manage-faculty/update-order/', views.update_faculty_order, name='update_faculty_order'),
    path('manage-faculty/bulk-delete/', views.bulk_delete_faculty, name='bulk_delete_faculty'),
    # Power users API
    path('api/power-users/', views.get_power_users, name='get_power_users'),
    # Publication management
    path('faculty/<int:faculty_id>/publications/', views.manage_publications, name='manage_publications'),
    path('faculty/<int:faculty_id>/publications/add/', views.add_publication, name='add_publication'),
    path('faculty/<int:faculty_id>/publications/add-multiple/', views.add_multiple_publications, name='add_multiple_publications'),
    path('faculty/<int:faculty_id>/publications/bulk-import/', views.bulk_import_publications, name='bulk_import_publications'),
    path('faculty/<int:faculty_id>/publications/confirm-single/', views.confirm_single_publication, name='confirm_single_publication'),
    path('publications/<int:publication_id>/edit/', views.edit_publication, name='edit_publication'),
    path('publications/<int:publication_id>/delete/', views.delete_publication, name='delete_publication'),
    path('faculty/<int:faculty_id>/publications/bulk-delete/', views.bulk_delete_publications, name='bulk_delete_publications'),
]

