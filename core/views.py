from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Field, Booking
from datetime import datetime
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import date
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from .forms import ProfileForm
from django.db.models.functions import TruncMonth
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

    initial = {
        'date': request.GET.get('date', ''),
        'start': request.GET.get('start', ''),
        'end': request.GET.get('end', ''),
    }
    
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

@login_required
def booking_receipt_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    html = render_to_string('booking_receipt.html', {'booking': booking})
    pdf = pdfkit.from_string(html, False)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{booking.id}.pdf"'
    return response

@staff_member_required
def admin_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'booking_receipt.html', {'booking': booking, 'admin_view': True})

@staff_member_required
def analytics_dashboard(request):
    # Total revenue (paid bookings)
    total_revenue = Booking.objects.filter(payment_status='paid').aggregate(Sum('amount'))['amount__sum'] or 0

    # Total bookings
    total_bookings = Booking.objects.count()

    # Approved bookings count
    approved_bookings = Booking.objects.filter(status='approved').count()

    # Monthly revenue summary
    monthly = (
        Booking.objects.filter(payment_status='paid')
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    # Convert to chart-friendly lists
    labels = [m['month'].strftime("%b %Y") for m in monthly]
    data = [float(m['total']) for m in monthly]

    context = {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'approved_bookings': approved_bookings,
        'labels': labels,
        'data': data,
    }
    return render(request, 'analytics_dashboard.html', context)


@login_required
def availability_calendar(request, field_id):
    field = get_object_or_404(Field, id=field_id)
    return render(request, 'availability_calendar.html', {'field': field})


@require_GET
def availability_api(request, field_id):
    field = get_object_or_404(Field, id=field_id)
    start = request.GET.get('start')  # FullCalendar passes ISO strings
    end = request.GET.get('end')

    # Parse to datetimes (YYYY-MM-DD or ISO)
    start_dt = datetime.fromisoformat(start[:19]) if start else None
    end_dt   = datetime.fromisoformat(end[:19]) if end else None

    # show approved bookings (users), staff can also see pending
    qs = Booking.objects.filter(field=field)
    if start_dt and end_dt:
        qs = qs.filter(date__range=[start_dt.date(), end_dt.date()])

    if request.user.is_staff:
        qs = qs.filter(status__in=['approved', 'pending'])
    else:
        qs = qs.filter(status='approved')

    events = []
    for b in qs:
        start_iso = f"{b.date}T{b.start_time}"
        end_iso   = f"{b.date}T{b.end_time}"
        color = '#198754' if b.status == 'approved' else '#ffc107'  # green / amber
        events.append({
            "id": b.id,
            "title": f"{b.field.name} - {b.user.username}",
            "start": start_iso,
            "end": end_iso,
            "color": color,
        })
    return JsonResponse(events, safe=False)


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully ✅")
            return redirect('profile')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'profile.html', {'form': form})
