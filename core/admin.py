from django.contrib import admin
from .models import Field, Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'field', 'date', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'date')
    actions = ['approve_bookings', 'reject_bookings']

    def approve_bookings(self, request, queryset):
        queryset.update(status='approved')
    approve_bookings.short_description = "Approve selected bookings"

    def reject_bookings(self, request, queryset):
        queryset.update(status='rejected')
    reject_bookings.short_description = "Reject selected bookings"

admin.site.register(Field)

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'price_per_hour', 'is_available')



