from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.core.validators import MinValueValidator, MaxValueValidator


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')
        
    def __str__(self):
        return f"{self.user.username} in {self.team.name}"
class Review(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.field.name} - {self.user.username} ({self.rating})"
class Field(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    price_per_hour = models.DecimalField(max_digits=7, decimal_places=2)
    is_available = models.BooleanField(default=True)
    photo = models.ImageField(
        upload_to='field_photos/',
        blank=True,
        null=True
    ) 

    def __str__(self):
        return self.name
    
class FieldImage(models.Model):
    field = models.ForeignKey(
        Field,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='field_gallery/')

    def __str__(self):
        return f"{self.field.name} Image"


class Booking(models.Model):
    STATUS_CHOICES = [('pending','Pending'), ('approved','Approved'), ('rejected','Rejected')]
    PAYMENT_CHOICES = [('unpaid','Unpaid'), ('paid','Paid'), ('refunded','Refunded')]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    amount = models.DecimalField(max_digits=9, decimal_places=2, default=0)  # auto-filled on create
    payment_status = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='unpaid')
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_ref = models.CharField(max_length=64, blank=True)  # optional txn/reference

    def clean(self):
        # time sanity
        if self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")
        # overlap (only approved block)
        overlap = Booking.objects.filter(
            field=self.field, date=self.date,
            start_time__lt=self.end_time, end_time__gt=self.start_time,
            status='approved'
        ).exclude(pk=self.pk)
        if overlap.exists():
            raise ValidationError("This field is already booked for that time slot.")

    def __str__(self):
        return f"{self.user.username} - {self.field.name} ({self.date})"

class TimeSlot(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='slots')
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.field.name}: {self.start_time} - {self.end_time}"
