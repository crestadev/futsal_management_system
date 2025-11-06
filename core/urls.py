from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('fields/', views.field_list, name='field_list'),
    path('book/<int:field_id>/', views.book_field, name='book_field'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
]
