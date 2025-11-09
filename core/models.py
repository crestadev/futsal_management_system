from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Field(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=150)
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    field = models.ForeignKey(Field, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} - {self.field.name} ({self.date})"

    
    def clean(self):
        overlap = Booking.objects.filter(
            field=self.field,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)
        if overlap.exists():
            raise ValidationError("This field is already booked for that time slot.")