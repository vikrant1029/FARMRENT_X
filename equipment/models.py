
from django.db import models
from django.contrib.auth.models import User


class Equipment(models.Model):

    CATEGORY_CHOICES = [
        ('Tractor', 'Tractor'),
        ('Harvester', 'Harvester'),
        ('Rotavator', 'Rotavator'),
        ('Seeder', 'Seeder'),
        ('Sprayer', 'Sprayer'),
        ('Plough', 'Plough'),
    ]

    LOCATION_CHOICES = [
        ('Karad', 'Karad'),
        ('Pune', 'Pune'),
        ('Satara', 'Satara'),
    ]

    name = models.CharField(max_length=100)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    location = models.CharField(
        max_length=50,
        choices=LOCATION_CHOICES
    )

    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=4.5
    )

    description = models.TextField()

    image_url = models.URLField(blank=True)

    available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Booking(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    customer_name = models.CharField(max_length=100)

    customer_phone = models.CharField(max_length=15)

    start_date = models.DateField()

    number_of_days = models.PositiveIntegerField()

    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        default='Confirmed'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.equipment.name}"


class Review(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='equipment_reviews'
    )

    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    rating = models.PositiveSmallIntegerField()

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'equipment'],
                name='unique_user_equipment_review'
            ),
            models.CheckConstraint(
                condition=models.Q(
                    rating__gte=1,
                    rating__lte=5
                ),
                name='review_rating_between_1_and_5'
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.equipment.name} ({self.rating}/5)"
        )


class Payment(models.Model):

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    PAYMENT_METHODS = [
        ('Demo UPI', 'Demo UPI'),
        ('Demo Card', 'Demo Card'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='Demo UPI'
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default='Pending'
    )

    transaction_id = models.CharField(
        max_length=50,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"Payment #{self.id} - "
            f"{self.booking.customer_name} - "
            f"{self.status}"
        )
