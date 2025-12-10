from django.urls import path
from . import views

app_name = 'people'

urlpatterns = [
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/<int:pk>/', views.faculty_detail, name='faculty_detail'),
    path('officers/', views.officer_list, name='officer_list'),
    path('officers/<int:pk>/', views.officer_detail, name='officer_detail'),
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]

