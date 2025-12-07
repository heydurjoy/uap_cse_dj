from django.urls import path
from . import views

app_name = 'designs'

urlpatterns = [
    path('feature-cards/', views.feature_cards_list, name='feature_cards_list'),
    path('feature-cards/<int:pk>/', views.feature_card_detail, name='feature_card_detail'),
]

