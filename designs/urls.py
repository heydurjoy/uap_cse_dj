from django.urls import path
from . import views

app_name = 'designs'

urlpatterns = [
    path('feature-cards/', views.feature_cards_list, name='feature_cards_list'),
    path('feature-cards/<int:pk>/', views.feature_card_detail, name='feature_card_detail'),
    path('manage-feature-cards/', views.manage_feature_cards, name='manage_feature_cards'),
    path('manage-feature-cards/create/', views.create_feature_card, name='create_feature_card'),
    path('manage-feature-cards/<int:pk>/edit/', views.edit_feature_card, name='edit_feature_card'),
    path('manage-feature-cards/<int:pk>/delete/', views.delete_feature_card, name='delete_feature_card'),
    path('manage-head-message/', views.manage_head_message, name='manage_head_message'),
    path('admission/<int:pk>/', views.admission_element_detail, name='admission_element_detail'),
    # Academic Calendar
    path('academic-calendar/', views.academic_calendar_view, name='academic_calendar'),
    path('academic-calendar/<int:pk>/pdf/', views.serve_academic_calendar_pdf, name='serve_academic_calendar_pdf'),
    path('manage-academic-calendars/', views.manage_academic_calendars, name='manage_academic_calendars'),
    path('manage-academic-calendars/create/', views.create_academic_calendar, name='create_academic_calendar'),
    path('manage-academic-calendars/<int:pk>/edit/', views.edit_academic_calendar, name='edit_academic_calendar'),
    path('manage-academic-calendars/<int:pk>/delete/', views.delete_academic_calendar, name='delete_academic_calendar'),
    # Hero Tags Management (Power Users Only)
    path('manage-hero-tags/', views.manage_hero_tags, name='manage_hero_tags'),
    path('manage-hero-tags/create/', views.create_hero_tag, name='create_hero_tag'),
    path('manage-hero-tags/<int:pk>/edit/', views.edit_hero_tag, name='edit_hero_tag'),
    path('manage-hero-tags/<int:pk>/delete/', views.delete_hero_tag, name='delete_hero_tag'),
    path('manage-hero-tags/update-order/', views.update_hero_tag_order, name='update_hero_tag_order'),
    # Curricula Management
    path('manage-curricula/', views.manage_curricula, name='manage_curricula'),
    path('manage-curricula/create/', views.create_curriculum, name='create_curriculum'),
    path('manage-curricula/<int:pk>/edit/', views.edit_curriculum, name='edit_curriculum'),
    path('manage-curricula/<int:pk>/delete/', views.delete_curriculum, name='delete_curriculum'),
    path('curricula/<int:pk>/pdf/', views.serve_curriculum_pdf, name='serve_curriculum_pdf'),
]

