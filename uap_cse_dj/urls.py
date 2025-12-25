"""
URL configuration for uap_cse_dj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.shortcuts import redirect, get_object_or_404
from . import views
from people.models import Faculty

def durjoy_faculty_redirect(request):
    """Redirect /1 to Durjoy Mistry's faculty detail page"""
    try:
        durjoy = Faculty.objects.select_related('base_user').filter(
            base_user__email='durjoy@uap-bd.edu'
        ).first()
        if durjoy:
            return redirect('people:faculty_detail', pk=durjoy.pk)
        else:
            return redirect('people:faculty_list')
    except:
        return redirect('people:faculty_list')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('1/', durjoy_faculty_redirect, name='durjoy_faculty'),
    path('', views.home, name='home'),
    path('themes/', views.themes, name='themes'),
    path('design-guidelines/', views.design_guidelines, name='design_guidelines'),
    path('system-documentation/', views.system_documentation, name='system_documentation'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('auth/google/', views.google_login, name='google_login'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('designs/', include('designs.urls')),
    path('people/', include('people.urls')),
    path('academics/', include('academics.urls')),
    path('office/', include('office.urls')),
    path('clubs/', include('clubs.urls')),
    path('features/', views.features, name='features'),
    path('credits/', views.credits, name='credits'),
    path('search/', views.search, name='search'),
]

# Serve media files in development and production
# In production, we need to serve media files since Railway's filesystem is ephemeral
# For a proper production setup, consider using cloud storage (S3, Cloudinary, etc.)
# Serve media files in both development and production
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Also serve static files in development (WhiteNoise handles this in production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
