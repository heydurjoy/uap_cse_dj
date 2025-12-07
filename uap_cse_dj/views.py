from django.shortcuts import render


def home(request):
    return render(request, 'home.html')


def themes(request):
    return render(request, 'themes.html')

