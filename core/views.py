from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Field, Booking
from datetime import datetime

def home(request):
    return render(request, 'home.html')

def field_list(request):
    fields = Field.objects.all()
    return render(request, 'field_list.html', {'fields': fields})

@login_required
def book_field(request, field_id):
    field = get_object_or_404(Field, id=field_id)
    
    if request.method == 'POST':
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        Booking.objects.create(
            user=request.user,
            field=field,
            date=date,
            start_time=start_time,
            end_time=end_time,
            is_confirmed=True
        )
        return redirect('my_bookings')
    
    return render(request, 'book_field.html', {'field': field})