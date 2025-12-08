from django.shortcuts import render
from designs.models import FeatureCard, HeroTags


def home(request):
    # Get active feature cards for the hero section
    all_cards = list(FeatureCard.objects.filter(is_active=True).order_by('sl_number'))
    # Start from the second card and include the rest
    feature_cards = all_cards[1:] if len(all_cards) > 1 else all_cards
    # Get all active hero tags ordered by serial number
    hero_tags = HeroTags.objects.filter(is_active=True).order_by('sl')
    # Use the first active feature card as the HoD highlight (editable via admin)
    hod_card = FeatureCard.objects.filter(is_active=True).order_by('sl_number').first()
    return render(request, 'home.html', {
        'feature_cards': feature_cards,
        'hero_tags': hero_tags,
        'hod_card': hod_card
    })


def themes(request):
    return render(request, 'themes.html')


def design_guidelines(request):
    return render(request, 'design_guidelines.html')


def login(request):
    return render(request, 'login.html')


def signup(request):
    return render(request, 'signup.html')

