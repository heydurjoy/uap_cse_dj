from django.shortcuts import render
from designs.models import FeatureCard


def home(request):
    # Get first 3 active feature cards for the hero section
    feature_cards = FeatureCard.objects.filter(is_active=True).order_by('sl_number')[:3]
    return render(request, 'home.html', {'feature_cards': feature_cards})


def themes(request):
    return render(request, 'themes.html')


def design_guidelines(request):
    return render(request, 'design_guidelines.html')

