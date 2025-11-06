from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Field, Booking
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log them in automatically
            messages.success(request, ' Account created successfully!')
            return redirect('home')
        else:
            messages.error(request, ' Please correct the errors below.')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


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

        conflict = Booking.objects.filter(
            field=field,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exists()

        if conflict:
            messages.error(request, " This field is already booked for that time slot. Please choose another.")
            return redirect('book_field', field_id=field.id)

        Booking.objects.create(
            user=request.user,
            field=field,
            date=date,
            start_time=start_time,
            end_time=end_time,
            is_confirmed=True
        )

        messages.success(request, f" Booking for {field.name} on {date} confirmed!")
        return redirect('my_bookings')

    return render(request, 'book_field.html', {'field': field})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-date')
    return render(request, 'my_bookings.html', {'bookings': bookings})