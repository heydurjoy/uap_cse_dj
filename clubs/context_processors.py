from .models import Club

def clubs(request):
    """
    Context processor to make clubs available to all templates.
    """
    clubs = Club.objects.all().order_by('sl', 'name')
    return {
        'clubs': clubs
    }












