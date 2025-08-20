from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# User Profile with Avatar
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.userprofile.save()


# Message logging model
class UserMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


# Travel package model
class TravelPackage(models.Model):
    CATEGORY_CHOICES = [
        ('beach', 'Beach Holiday'),
        ('mountain', 'Mountain Adventure'),
        ('city', 'City Tour'),
    ]

    name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.name} - {self.destination}"


# models.py
class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    amenities = models.TextField()
    image = models.ImageField(upload_to='hotel_images/', default='hotel_images/default.webp', null=True, blank=True)  # NEW FIELD

    def __str__(self):
        return self.name



# Flight model
from django.db import models
class Flight(models.Model):
    flight_number = models.CharField(max_length=20, unique=True)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seats_available = models.IntegerField()
    def __str__(self):
        return f"{self.flight_number}: {self.origin} to {self.destination}"
    
# Booking model
class Booking(models.Model):
    BOOKING_TYPE_CHOICES = [
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('package', 'Travel Package'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_type = models.CharField(max_length=10, choices=BOOKING_TYPE_CHOICES)
    reference_id = models.CharField(max_length=100)
    booked_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Confirmed')

    class Meta:
        ordering = ['-booked_on']

    def __str__(self):
        return f"{self.user.username} - {self.booking_type} - {self.status}"


# Hotel booking model
class HotelBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hotel_bookings')
    hotel_name = models.CharField(max_length=255)
    check_in_date = models.DateField()
    nights = models.IntegerField()
    guests = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.hotel_name} ({self.check_in_date})"

class FlightBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flight_bookings')
    departure = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    travel_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.departure} to {self.destination} on {self.travel_date}"
