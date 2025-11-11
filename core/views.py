from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Field, Booking
from datetime import datetime
from decimal import Decimal
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required


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

        # conflict only against approved
        conflict = Booking.objects.filter(
            field=field, date=date,
            start_time__lt=end_time, end_time__gt=start_time,
            status='approved'
        ).exists()
        if conflict:
            messages.error(request, "⚠️ This field is already booked for that time slot.")
            return redirect('book_field', field_id=field.id)

        # compute hours * price_per_hour
        # combine to datetimes for duration
        start_dt = datetime.fromisoformat(f"{date} {start_time}")
        end_dt   = datetime.fromisoformat(f"{date} {end_time}")
        if end_dt <= start_dt:
            messages.error(request, "⚠️ End time must be after start time.")
            return redirect('book_field', field_id=field.id)

        duration_hours = Decimal((end_dt - start_dt).seconds) / Decimal(3600)
        amount = (duration_hours * Decimal(field.price_per_hour)).quantize(Decimal("0.01"))

        Booking.objects.create(
            user=request.user,
            field=field,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status='pending',
            amount=amount,            # 💰 save computed amount
            payment_status='unpaid'
        )

        messages.success(request, f"✅ Booking request submitted! Amount: Rs. {amount}. Awaiting admin approval.")
        return redirect('my_bookings')

    return render(request, 'book_field.html', {'field': field})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-date')
    return render(request, 'my_bookings.html', {'bookings': bookings})

@staff_member_required
def admin_dashboard(request):
    bookings = Booking.objects.all().order_by('-date', '-start_time')
    return render(request, 'admin_dashboard.html', {'bookings': bookings})

@staff_member_required
def update_booking_status(request, booking_id, status):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.status = status
        booking.save()
        messages.success(request, f"Booking for {booking.field.name} marked as {status.title()}.")
    return redirect('admin_dashboard')



@staff_member_required
def update_payment_status(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        if action == 'paid':
            booking.payment_status = 'paid'
            booking.payment_date = timezone.now()
            messages.success(request, f"Marked as PAID (Rs. {booking.amount}).")
        elif action == 'unpaid':
            booking.payment_status = 'unpaid'
            booking.payment_date = None
            messages.success(request, "Marked as UNPAID.")
        elif action == 'refunded':
            booking.payment_status = 'refunded'
            messages.success(request, "Marked as REFUNDED.")
        booking.save()
    return redirect('admin_dashboard')

