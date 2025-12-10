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
    
    # Class Routine URLs
    path('routines/', views.routine_list, name='routine_list'),
    path('routines/<int:pk>/', views.routine_detail, name='routine_detail'),
    path('routines/manage/', views.manage_routines, name='manage_routines'),
    path('routines/create/', views.create_routine, name='create_routine'),
    path('routines/<int:pk>/edit/', views.edit_routine, name='edit_routine'),
    path('routines/<int:pk>/delete/', views.delete_routine, name='delete_routine'),
    
    # Admission Results Public Search URLs
    path('admissions/results/', views.search_admission_results, name='search_admission_results'),
    path('admissions/results/<int:pk>/pdf/', views.serve_admission_pdf, name='serve_admission_pdf'),
    path('api/admissions/slots/', views.get_available_slots, name='get_available_slots'),
    
    # Admission Results Management URLs
    path('admissions/manage/', views.manage_admission_results, name='manage_admission_results'),
    path('admissions/create/', views.create_admission_result, name='create_admission_result'),
    path('admissions/<int:pk>/edit/', views.edit_admission_result, name='edit_admission_result'),
    path('admissions/<int:pk>/delete/', views.delete_admission_result, name='delete_admission_result'),
]

