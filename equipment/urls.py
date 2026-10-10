from django.urls import path
from . import views

urlpatterns = [
    path('', views.equipment_list, name='equipment_list'),

    path(
        'details/<int:equipment_id>/',
        views.equipment_detail,
        name='equipment_detail'
    ),

    path(
        'book/<int:equipment_id>/',
        views.book_equipment,
        name='book_equipment'
    ),

    path(
        'payment/<int:booking_id>/',
        views.payment_page,
        name='payment_page'
    ),

    path(
        'booking-success/<int:booking_id>/',
        views.booking_success,
        name='booking_success'
    ),

    path('my-bookings/', views.my_bookings, name='my_bookings'),

    path(
        'cancel-booking/<int:booking_id>/',
        views.cancel_booking,
        name='cancel_booking'
    ),

    path(
        'review/<int:equipment_id>/',
        views.add_review,
        name='add_review'
    ),

path(
    'admin-dashboard/',
    views.admin_dashboard,
    name='admin_dashboard'
),
]