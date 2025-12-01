from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # --------------------------
    # PUBLIC
    # --------------------------
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('fields/', views.field_list, name='field_list'),
    path('field/<int:field_id>/', views.field_detail, name='field_detail'),

    # --------------------------
    # BOOKINGS
    # --------------------------
    path('book/<int:field_id>/', views.book_field, name='book_field'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # --------------------------
    # RECEIPTS
    # --------------------------
    path('receipt/<int:booking_id>/', views.booking_receipt, name='booking_receipt'),
    path('admin-receipt/<int:booking_id>/', views.admin_receipt, name='admin_receipt'),
    # Optional PDF export (if using pdfkit)
    path('receipt-pdf/<int:booking_id>/', views.booking_receipt_pdf, name='booking_receipt_pdf'),

    # --------------------------
    # ADMIN DASHBOARD
    # --------------------------
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('update-booking/<int:booking_id>/<str:status>/', 
         views.update_booking_status, name='update_booking_status'),

    path('update-payment/<int:booking_id>/<str:action>/',
         views.update_payment_status, name='update_payment_status'),

    # --------------------------
    # ANALYTICS
    # --------------------------
    path('analytics-dashboard/', views.analytics_dashboard, name='analytics_dashboard'),

    # --------------------------
    # SINGLE FIELD CALENDAR
    # --------------------------
    path('calendar/<int:field_id>/', views.availability_calendar, name='availability_calendar'),
    path('api/availability/<int:field_id>/', views.availability_api, name='availability_api'),

    # --------------------------
    # ALL FIELDS CALENDAR
    # --------------------------
    path('calendar-all/', views.all_fields_calendar, name='all_fields_calendar'),
    path('api/calendar-all/', views.all_fields_api, name='all_fields_api'),

    # --------------------------
    # PROFILE & ACCOUNT
    # --------------------------
    path('profile/', views.profile_view, name='profile'),

    path(
        'change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='change_password.html',
            success_url='/profile/'
        ),
        name='change_password'
    ),

    path('export-excel/', views.export_bookings_excel, name='export_excel'),

]
path("khalti/callback/<int:booking_id>/", views.khalti_callback, name="khalti_callback")
path('field/<int:field_id>/review/', views.add_review, name='add_review'),
path("teams/", views.my_teams, name="my_teams"),
path("teams/create/", views.create_team, name="create_team"),
path("teams/join/<int:team_id>/", views.join_team, name="join_team"),
path('matches/', views.match_list, name='match_list'),
path('matches/schedule/', views.schedule_match, name='schedule_match'),
path('matches/<int:match_id>/score/', views.report_score, name='report_score'),
path("leaderboard/", views.leaderboard, name="leaderboard"),

