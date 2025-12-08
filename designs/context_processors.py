from .models import AdmissionElement

def admission_elements(request):
    """
    Context processor to make admission elements available to all templates.
    """
    admission_elements = AdmissionElement.objects.all().order_by('sl')
    return {
        'admission_elements': admission_elements
    }

