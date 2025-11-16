from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('fields/', views.field_list, name='field_list'),
    path('book/<int:field_id>/', views.book_field, name='book_field'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update-booking/<int:booking_id>/<str:status>/', views.update_booking_status, name='update_booking_status'),

    # Receipts
    path('receipt/<int:booking_id>/', views.booking_receipt, name='booking_receipt'),
    path('admin-receipt/<int:booking_id>/', views.admin_receipt, name='admin_receipt'),

    # Analytics
    path('analytics-dashboard/', views.analytics_dashboard, name='analytics_dashboard'),

    # Single-field calendar
    path('calendar/<int:field_id>/', views.availability_calendar, name='availability_calendar'),
    path('api/availability/<int:field_id>/', views.availability_api, name='availability_api'),

    # Multi-field calendar
    path('calendar-all/', views.all_fields_calendar, name='all_fields_calendar'),
    path('api/calendar-all/', views.all_fields_api, name='all_fields_api'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Change password
    path(
        'change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='change_password.html',
            success_url='/profile/'
        ),
        name='change_password'
    ),
]
