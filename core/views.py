from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from django.views.decorators.http import require_GET
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import TruncMonth

from .models import Field, Booking
from .forms import ProfileForm

from datetime import datetime
from decimal import Decimal

from django.template.loader import render_to_string
import pdfkit   # ONLY if you use PDF generation


# -----------------------------
# PUBLIC PAGES
# -----------------------------

def home(request):
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


def field_list(request):
    fields = Field.objects.all()
    return render(request, 'field_list.html', {'fields': fields})


# -----------------------------
# BOOKING
# -----------------------------

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

        # check conflict with approved bookings
        conflict = Booking.objects.filter(
            field=field,
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status='approved'
        ).exists()

        if conflict:
            messages.error(request, "⚠️ This field is already booked for that time slot.")
            return redirect('book_field', field_id=field.id)

        # compute price
        start_dt = datetime.fromisoformat(f"{date} {start_time}")
        end_dt = datetime.fromisoformat(f"{date} {end_time}")

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
            amount=amount,
            payment_status='unpaid'
        )

        messages.success(request, f"Booking submitted! Amount: Rs. {amount}. Awaiting approval.")
        return redirect('my_bookings')

    return render(request, 'book_field.html', {'field': field, 'initial': initial})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-date', '-start_time')
    return render(request, 'my_bookings.html', {'bookings': bookings})


# -----------------------------
# RECEIPTS
# -----------------------------

@login_required
def booking_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return render(request, 'booking_receipt.html', {'booking': booking})


@staff_member_required
def admin_receipt(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'booking_receipt.html', {'booking': booking, 'admin_view': True})


@login_required
def booking_receipt_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    html = render_to_string('booking_receipt.html', {'booking': booking})
    pdf = pdfkit.from_string(html, False)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=receipt_{booking.id}.pdf'
    return response


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------

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
        messages.success(request, f"Booking updated to {status.title()}.")
    
    return redirect('admin_dashboard')


@staff_member_required
def update_payment_status(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        if action == "paid":
            booking.payment_status = "paid"
            booking.payment_date = timezone.now()
        elif action == "unpaid":
            booking.payment_status = "unpaid"
            booking.payment_date = None
        elif action == "refunded":
            booking.payment_status = "refunded"

        booking.save()
        messages.success(request, "Payment status updated.")

    return redirect('admin_dashboard')


# -----------------------------
# ANALYTICS
# -----------------------------

@staff_member_required
def analytics_dashboard(request):
    total_revenue = Booking.objects.filter(payment_status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    total_bookings = Booking.objects.count()
    approved_bookings = Booking.objects.filter(status='approved').count()

    monthly = (
        Booking.objects.filter(payment_status='paid')
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )

    labels = [m['month'].strftime("%b %Y") for m in monthly]
    data = [float(m['total']) for m in monthly]

    return render(request, 'analytics_dashboard.html', {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'approved_bookings': approved_bookings,
        'labels': labels,
        'data': data,
    })


# -----------------------------
# CALENDAR (SINGLE FIELD)
# -----------------------------

@login_required
def availability_calendar(request, field_id):
    field = get_object_or_404(Field, id=field_id)
    return render(request, 'availability_calendar.html', {'field': field})


@require_GET
def availability_api(request, field_id):
    field = get_object_or_404(Field, id=field_id)

    qs = Booking.objects.filter(field=field)
    if request.user.is_staff:
        qs = qs.filter(status__in=['approved', 'pending'])
    else:
        qs = qs.filter(status='approved')

    events = [{
        "id": b.id,
        "title": f"{b.field.name}",
        "start": f"{b.date}T{b.start_time}",
        "end": f"{b.date}T{b.end_time}",
        "color": "#28a745" if b.status == "approved" else "#ffc107",
    } for b in qs]

    return JsonResponse(events, safe=False)


# -----------------------------
# CALENDAR (ALL FIELDS)
# -----------------------------

@login_required
def all_fields_calendar(request):
    fields = Field.objects.all()
    return render(request, 'all_fields_calendar.html', {'fields': fields})


@require_GET
def all_fields_api(request):
    fields = Field.objects.all()
    events = []

    colors = ["#1abc9c", "#3498db", "#9b59b6", "#f39c12", "#e74c3c", "#2ecc71", "#34495e"]

    for field in fields:
        qs = Booking.objects.filter(field=field)

        if request.user.is_staff:
            qs = qs.filter(status__in=['approved', 'pending'])
        else:
            qs = qs.filter(status='approved')

        field_color = colors[(field.id - 1) % len(colors)]

        for b in qs:
            events.append({
                "id": b.id,
                "title": f"{field.name}",
                "start": f"{b.date}T{b.start_time}",
                "end": f"{b.date}T{b.end_time}",
                "color": field_color,
            })

    return JsonResponse(events, safe=False)


# -----------------------------
# PROFILE
# -----------------------------

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'profile.html', {'form': form})
