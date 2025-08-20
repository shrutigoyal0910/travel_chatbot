from django.contrib import admin
from .models import UserMessage, TravelPackage, Hotel, Flight, Booking, HotelBooking, UserProfile

admin.site.register(UserMessage)
admin.site.register(TravelPackage)
admin.site.register(Hotel)
admin.site.register(Flight)
admin.site.register(Booking)
admin.site.register(UserProfile)
@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'hotel_name', 'check_in_date', 'nights', 'guests', 'created_at')
from .models import FlightBooking

@admin.register(FlightBooking)
class FlightBookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'departure', 'destination', 'travel_date', 'created_at')
