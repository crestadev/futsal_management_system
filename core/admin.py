from django.contrib import admin
from .models import Field, Review, Booking, TimeSlot, FieldImage, Match, Team


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('field', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'field')

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


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'price_per_hour', 'is_available')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('field', 'start_time', 'end_time')
    list_filter = ('field',)

class FieldImageInline(admin.TabularInline):
    model = FieldImage
    extra = 1  

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'price_per_hour', 'is_available')
    inlines = [FieldImageInline]

admin.site.register(FieldImage)

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('team_a', 'team_b', 'field', 'date', 'status')
    list_filter = ('status', 'field', 'date')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_public', 'created_at')
    filter_horizontal = ('members',)