from django.contrib import admin
from .models import Equipment, Booking, Review, Payment


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'location',
        'price_per_day',
        'rating',
        'available',
    )
    list_filter = ('category', 'location', 'available')
    search_fields = ('name', 'location', 'category')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'customer_name',
        'customer_phone',
        'equipment',
        'start_date',
        'number_of_days',
        'total_price',
        'status',
        'created_at',
    )
    list_filter = ('status', 'start_date')
    search_fields = (
        'customer_name',
        'customer_phone',
        'equipment__name',
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('equipment', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('equipment__name', 'user__username', 'comment')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'booking',
        'amount',
        'payment_method',
        'status',
        'transaction_id',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = (
        'transaction_id',
        'booking__customer_name',
        'booking__equipment__name',
    )