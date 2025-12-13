from django.shortcuts import render, get_object_or_404
from easy_thumbnails.files import get_thumbnailer
from .models import FeatureCard, AdmissionElement

def feature_cards_list(request):
    """Display all active feature cards"""
    cards = FeatureCard.objects.filter(is_active=True).order_by('sl_number')
    return render(request, 'designs/feature_cards_list.html', {'cards': cards})

def feature_card_detail(request, pk):
    """Display detailed view of a feature card"""
    card = get_object_or_404(FeatureCard, pk=pk, is_active=True)
    return render(request, 'designs/feature_card_detail.html', {'card': card})

def admission_element_detail(request, pk):
    """Display admission element content dynamically"""
    element = get_object_or_404(AdmissionElement, pk=pk)
    return render(request, 'designs/admission_element_detail.html', {'element': element})

