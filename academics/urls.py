from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('courses/manage/', views.manage_courses, name='manage_courses'),
    path('courses/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('courses/delete/', views.delete_courses, name='delete_courses'),
]

