
from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Avg, Sum
from django.db import transaction
from django.utils.crypto import get_random_string

from .models import Equipment, Booking, Review, Payment


# ==========================================
# EQUIPMENT LIST + SEARCH + FILTER
# ==========================================

def equipment_list(request):
    equipments = Equipment.objects.filter(available=True)

    search_query = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()
    location = request.GET.get('location', '').strip()

    if search_query:
        equipments = equipments.filter(name__icontains=search_query)

    valid_categories = [
        choice[0] for choice in Equipment.CATEGORY_CHOICES
    ]
    valid_locations = [
        choice[0] for choice in Equipment.LOCATION_CHOICES
    ]

    if category in valid_categories:
        equipments = equipments.filter(category=category)

    if location in valid_locations:
        equipments = equipments.filter(location=location)

    context = {
        'equipments': equipments,
        'search_query': search_query,
        'selected_category': category,
        'selected_location': location,
        'categories': Equipment.CATEGORY_CHOICES,
        'locations': Equipment.LOCATION_CHOICES,
    }

    return render(request, 'equipment/equipment_list.html', context)


# ==========================================
# EQUIPMENT DETAIL + REVIEWS
# ==========================================

def equipment_detail(request, equipment_id):
    equipment = get_object_or_404(
        Equipment,
        id=equipment_id
    )

    reviews = Review.objects.filter(
        equipment=equipment
    ).select_related('user').order_by('-created_at')

    average_rating = reviews.aggregate(
        average=Avg('rating')
    )['average']

    user_review = None

    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    return render(
        request,
        'equipment/equipment_detail.html',
        {
            'equipment': equipment,
            'reviews': reviews,
            'average_rating': average_rating,
            'user_review': user_review,
        }
    )


# ==========================================
# BOOK EQUIPMENT
# ==========================================

@login_required
def book_equipment(request, equipment_id):
    equipment = get_object_or_404(
        Equipment,
        id=equipment_id,
        available=True
    )

    if request.method == 'POST':
        customer_name = request.POST.get(
            'customer_name', ''
        ).strip()

        customer_phone = request.POST.get(
            'customer_phone', ''
        ).strip()

        start_date_value = request.POST.get('start_date', '')
        days_value = request.POST.get('number_of_days', '1')

        error = None
        start_date = None

        try:
            start_date = date.fromisoformat(start_date_value)
        except (ValueError, TypeError):
            error = 'Please enter a valid booking date.'

        try:
            number_of_days = int(days_value)
        except (ValueError, TypeError):
            number_of_days = 0

        if not customer_name:
            error = 'Please enter your full name.'

        elif len(customer_name) > 100:
            error = 'Name must be 100 characters or fewer.'

        elif not customer_phone:
            error = 'Please enter your phone number.'

        elif not customer_phone.replace('+', '').replace(' ', '').isdigit():
            error = 'Please enter a valid phone number.'

        elif len(customer_phone) > 15:
            error = 'Phone number must be 15 characters or fewer.'

        elif start_date is None:
            error = 'Please enter a valid booking date.'

        elif start_date < date.today():
            error = 'Booking date cannot be in the past.'

        elif number_of_days < 1 or number_of_days > 365:
            error = 'Booking duration must be between 1 and 365 days.'

        if error:
            return render(
                request,
                'equipment/booking.html',
                {
                    'equipment': equipment,
                    'error': error,
                }
            )

        booking = Booking.objects.create(
            user=request.user,
            equipment=equipment,
            customer_name=customer_name,
            customer_phone=customer_phone,
            start_date=start_date,
            number_of_days=number_of_days,
            total_price=equipment.price_per_day * number_of_days,
            status='Pending',
        )

        messages.info(
            request,
            'Booking details saved. Complete demo payment to confirm.'
        )

        return redirect('payment_page', booking_id=booking.id)

    return render(
        request,
        'equipment/booking.html',
        {'equipment': equipment}
    )


# ==========================================
# DEMO PAYMENT PAGE
# ==========================================

@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if booking.status == 'Cancelled':
        messages.warning(
            request,
            'This booking has been cancelled and cannot be paid.'
        )
        return redirect('my_bookings')

    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'amount': booking.total_price,
            'status': 'Pending',
            'payment_method': 'Demo UPI',
        }
    )

    if payment.status == 'Success' and booking.status == 'Confirmed':
        return redirect('booking_success', booking_id=booking.id)

    if request.method == 'POST':
        method = request.POST.get('payment_method', '')

        if method not in ['Demo UPI', 'Demo Card']:
            messages.error(
                request,
                'Please select a valid demo payment method.'
            )
            return redirect('payment_page', booking_id=booking.id)

        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(
                id=booking.id,
                user=request.user
            )

            payment = Payment.objects.select_for_update().get(
                booking=booking
            )

            if booking.status == 'Cancelled':
                messages.error(
                    request,
                    'This booking has been cancelled.'
                )
                return redirect('my_bookings')

            if payment.status == 'Success':
                if booking.status == 'Confirmed':
                    return redirect(
                        'booking_success',
                        booking_id=booking.id
                    )

                messages.error(
                    request,
                    'Payment already exists. Please contact the administrator.'
                )
                return redirect('my_bookings')

            payment.amount = booking.total_price
            payment.payment_method = method
            payment.status = 'Success'
            payment.transaction_id = (
                'DEMO-' + get_random_string(12).upper()
            )
            payment.save()

            booking.status = 'Confirmed'
            booking.save(update_fields=['status'])

        messages.success(
            request,
            'Demo payment successful! No real money was charged.'
        )

        return redirect('booking_success', booking_id=booking.id)

    return render(
        request,
        'equipment/payment.html',
        {
            'booking': booking,
            'payment': payment,
        }
    )


# ==========================================
# BOOKING SUCCESS / RECEIPT
# ==========================================

@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('equipment', 'user'),
        id=booking_id,
        user=request.user
    )

    payment = Payment.objects.filter(
        booking=booking,
        status='Success'
    ).first()

    if payment is None or booking.status != 'Confirmed':
        messages.warning(
            request,
            'Please complete your payment before viewing the receipt.'
        )
        return redirect('payment_page', booking_id=booking.id)

    return render(
        request,
        'equipment/booking_success.html',
        {
            'booking': booking,
            'payment': payment,
        }
    )


# ==========================================
# MY BOOKINGS
# ==========================================

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('equipment').order_by('-created_at')

    return render(
        request,
        'equipment/my_bookings.html',
        {'bookings': bookings}
    )


# ==========================================
# CANCEL BOOKING
# ==========================================

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if request.method != 'POST':
        return redirect('my_bookings')

    if booking.status == 'Confirmed':
        booking.status = 'Cancelled'
        booking.save(update_fields=['status'])

        messages.success(
            request,
            'Your booking has been cancelled.'
        )

    elif booking.status == 'Pending':
        booking.status = 'Cancelled'
        booking.save(update_fields=['status'])

        messages.success(
            request,
            'Your pending booking has been cancelled.'
        )

    else:
        messages.warning(
            request,
            'This booking cannot be cancelled.'
        )

    return redirect('my_bookings')


# ==========================================
# ADD / UPDATE REVIEW
# ==========================================

@login_required
def add_review(request, equipment_id):
    equipment = get_object_or_404(
        Equipment,
        id=equipment_id
    )

    if request.method != 'POST':
        return redirect(
            'equipment_detail',
            equipment_id=equipment.id
        )

    rating_value = request.POST.get('rating', '')
    comment = request.POST.get('comment', '').strip()

    try:
        rating = int(rating_value)
    except (ValueError, TypeError):
        messages.error(
            request,
            'Please select a valid rating.'
        )
        return redirect(
            'equipment_detail',
            equipment_id=equipment.id
        )

    if rating < 1 or rating > 5 or not comment:
        messages.error(
            request,
            'Select a rating from 1 to 5 and enter your review.'
        )
        return redirect(
            'equipment_detail',
            equipment_id=equipment.id
        )

    review, created = Review.objects.update_or_create(
        user=request.user,
        equipment=equipment,
        defaults={
            'rating': rating,
            'comment': comment,
        }
    )

    messages.success(
        request,
        'Your review was submitted successfully!'
        if created
        else 'Your review was updated successfully!'
    )

    return redirect(
        'equipment_detail',
        equipment_id=equipment.id
    )


# ==========================================
# ADMIN DASHBOARD + ANALYTICS
# ==========================================

@staff_member_required
def admin_dashboard(request):
    total_equipment = Equipment.objects.count()

    available_equipment = Equipment.objects.filter(
        available=True
    ).count()

    total_bookings = Booking.objects.count()

    confirmed_bookings = Booking.objects.filter(
        status='Confirmed'
    ).count()

    pending_bookings = Booking.objects.filter(
        status='Pending'
    ).count()

    cancelled_bookings = Booking.objects.filter(
        status='Cancelled'
    ).count()

    successful_payments = Payment.objects.filter(
        status='Success'
    )

    successful_payment_count = successful_payments.count()

    total_demo_payments = (
        successful_payments.aggregate(
            total=Sum('amount')
        )['total'] or 0
    )

    recent_bookings = (
        Booking.objects.select_related('equipment', 'user')
        .order_by('-created_at')[:5]
    )

    context = {
        'total_equipment': total_equipment,
        'available_equipment': available_equipment,
        'total_bookings': total_bookings,
        'confirmed_bookings': confirmed_bookings,
        'pending_bookings': pending_bookings,
        'cancelled_bookings': cancelled_bookings,
        'successful_payment_count': successful_payment_count,
        'total_demo_payments': total_demo_payments,
        'recent_bookings': recent_bookings,
    }

    return render(
        request,
        'equipment/admin_dashboard.html',
        context
    )
