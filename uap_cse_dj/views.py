from django.shortcuts import render
from designs.models import FeatureCard, HeroTags


def home(request):
    # Get first 3 active feature cards for the hero section
    feature_cards = FeatureCard.objects.filter(is_active=True).order_by('sl_number')[:3]
    # Get all active hero tags ordered by serial number
    hero_tags = HeroTags.objects.filter(is_active=True).order_by('sl')
    return render(request, 'home.html', {
        'feature_cards': feature_cards,
        'hero_tags': hero_tags
    })


def themes(request):
    return render(request, 'themes.html')


def design_guidelines(request):
    return render(request, 'design_guidelines.html')


def login(request):
    return render(request, 'login.html')


def signup(request):
    return render(request, 'signup.html')

