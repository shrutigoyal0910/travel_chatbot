from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserMessage, TravelPackage, Hotel, Flight, Booking, UserProfile
)

class CombinedUserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar_url']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        try:
            profile = obj.userprofile  # Assumes related_name='userprofile' for OneToOneField
            if profile and profile.avatar and hasattr(profile.avatar, 'url'):
                if request:
                    return request.build_absolute_uri(profile.avatar.url)
                return profile.avatar.url  # Fallback if no request context
        except UserProfile.DoesNotExist:
            pass
        return None

class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta: 
        model = UserProfile
        fields = ['avatar_url']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if request and obj.avatar and hasattr(obj.avatar, 'url'):
            return request.build_absolute_uri(obj.avatar.url)
        elif obj.avatar and hasattr(obj.avatar, 'url'):
            return obj.avatar.url  # Fallback if no request context
        return None

class UserMessageSerializer(serializers.ModelSerializer):
    user = CombinedUserSerializer(read_only=True)  # Updated to use CombinedUserSerializer

    class Meta:
        model = UserMessage
        fields = '__all__'

class TravelPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPackage
        fields = '__all__'

class HotelSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['name', 'location', 'rating', 'price_per_night', 'amenities', 'image']

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None



class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    user = CombinedUserSerializer(read_only=True)  # Updated to use CombinedUserSerializer

    class Meta:
        model = Booking
        fields = '__all__'