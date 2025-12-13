from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('courses/', views.courses_list, name='courses_list'),
    path('courses/manage/', views.manage_courses, name='manage_courses'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('courses/delete/', views.delete_courses, name='delete_courses'),
]

