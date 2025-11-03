from django.shortcuts import render, get_object_or_404, redirect
from .models import Field



def home(request):
    return render(request, 'home.html')

def field_list(request):
    fields = Field.objects.all()
    return render(request, 'field_list.html', {'fields': fields})