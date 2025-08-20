from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    chat_with_rasa,
    chatbot_page,
    login_view,
    signup_view,
    clear_chat_history,
    TravelPackageListAPIView,
    HotelListAPIView,
    FlightListAPIView,
    BookingListAPIView,
    UserMessageListAPIView,
    UserProfileAPIView,
    test_api,
    chat_with_ai,
)

urlpatterns = [
    # Chatbot views
    path('', chatbot_page, name='chatbot_page'),
    path('chat/', chat_with_rasa, name='chat_with_rasa'),
    path('chat/ai/', chat_with_ai, name='chat_with_ai'),
    path('clear_chat/', clear_chat_history, name='clear_chat'),
    path('test-api/', test_api, name='test_api'),  # Add the test API endpoint

    # Authentication views
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', signup_view, name='signup'),
    path('api/profile/', UserProfileAPIView.as_view(), name='user-profile'),

    # API Endpoints
    path('api/travel-packages/', TravelPackageListAPIView.as_view(), name='api-travel-packages'),
    path('api/hotels/', HotelListAPIView.as_view(), name='api-hotels'),
    path('api/flights/', FlightListAPIView.as_view(), name='api-flights'),
    path('api/bookings/', BookingListAPIView.as_view(), name='api-bookings'),
    path('api/messages/', UserMessageListAPIView.as_view(), name='api-messages'),
]

