import boto3
import json
import requests
import logging
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from decouple import config  
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView

from rest_framework import generics
from .forms import SignupForm
from .models import TravelPackage, Hotel, Flight, Booking, UserMessage
from .serializers import (
    TravelPackageSerializer, HotelSerializer,
    FlightSerializer, BookingSerializer,
    UserMessageSerializer, CombinedUserSerializer
)

# Set up logging
logger = logging.getLogger(__name__)

# --- Normal Django Views ---

@login_required
def clear_chat_history(request):
    """Delete all messages for the current user."""
    if request.method != "POST":
        logger.warning(f"Invalid method {request.method} for clear_chat_history by user {request.user.username}")
        return JsonResponse({"error": "Method not allowed"}, status=405)

    UserMessage.objects.filter(user=request.user).delete()
    logger.info(f"Chat history cleared for user {request.user.username}")
    return JsonResponse({"status": "success", "message": "Chat history cleared."})

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f"New user signed up: {user.username}")
            return redirect('chatbot_page')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

@csrf_exempt
def chat_with_rasa(request):
    """Handle chat requests using Rasa with direct flight booking logic."""
    if request.method != "POST":
        logger.warning(f"Invalid method {request.method} for chat_with_rasa")
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        logger.info(f"Received message: {user_message}")

        if not user_message:
            logger.warning("Empty message received in chat_with_rasa")
            return JsonResponse({"reply": "Please enter a message."})

        # Handle specific intents directly
        if user_message.lower() == "book_flight":
            flights = Flight.objects.all()[:3]
            serializer = FlightSerializer(flights, many=True)
            cards = [
                {
                    "title": flight["flight_number"],
                    "subtitle": f"{flight['origin']} to {flight['destination']}",
                    "price": str(flight["price"]),
                    "departure": flight["departure_time"],
                    "seats": str(flight["seats_available"]),
                    "buttons": [{"title": "Book Now", "payload": f'book_flight{{"flight_number": "{flight["flight_number"]}"}}'}]
                } for flight in serializer.data
            ]
            return JsonResponse({
                "reply": f"Found {len(cards)} flights.",
                "custom": {"type": "flight_cards", "cards": cards}
            })

        sender_id = request.user.username if request.user.is_authenticated else "anonymous"

        rasa_response = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",
            json={"sender": sender_id, "message": user_message},
            timeout=10
        )
        rasa_response.raise_for_status()
        messages = rasa_response.json()

        bot_reply = " ".join([msg.get("text", "") for msg in messages]).strip() or \
                    "Sorry, I didn't understand that."
        buttons = next((msg["buttons"] for msg in messages if "buttons" in msg), [])
        custom_payload = next((msg["custom"] for msg in messages if "custom" in msg), None)

        if request.user.is_authenticated:
            UserMessage.objects.create(
                user=request.user,
                message=user_message,
                response=bot_reply
            )
            logger.info(f"Message saved for user {request.user.username}: {user_message}")

        return JsonResponse({
            "reply": bot_reply,
            "buttons": buttons,
            "custom": custom_payload
        })

    except requests.exceptions.RequestException as e:
        logger.error(f"Rasa server error: {str(e)}")
        return JsonResponse({"reply": "Error communicating with Rasa server."})
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_rasa: {str(e)}")
        return JsonResponse({"reply": "Something went wrong."})
    

@csrf_exempt
def chat_with_ai(request):
    if request.method != "POST":
        logger.warning(f"Invalid method {request.method} for chat_with_rasa")
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        logger.info(f"Request body: {request.body.decode('utf-8')}")
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        logger.info(f"Received message: {user_message}")

        if not user_message:
            logger.warning("Empty message received in chat_with_rasa")
            return JsonResponse({"reply": "Please enter a message."})

        # Prepare headers and payload for OpenRouter API
        headers = {
            "Authorization": f"Bearer {config('DEEPSEEK_API_KEY')}",
            "HTTP-Referer": "http://127.0.0.1:8000",  # Update with your site URL
            "X-Title": "Qyra Chatbot",  # Update with your site name
            "Content-Type": "application/json"
        }
        payload = {
            "model": "deepseek/deepseek-r1-0528:free",
            "messages": [
                {"role": "system", "content": "You are Qyra, a helpful travel assistant. Provide travel-related advice, flight/hotel information, or travel tips based on the user's input. If the input is vague (e.g., 'hello'), suggest travel options like 'book_flight' or 'how can i book hotel'.  Keep responses concise (max 30 words for simple replies, longer for detailed options)."},
                {"role": "user", "content": user_message}
            ]
        }
        logger.info(f"Sending payload to OpenRouter: {json.dumps(payload)}")

        # Call OpenRouter API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info("OpenRouter response received")
        bot_reply = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        logger.info(f"OpenRouter response: {bot_reply}")

        # Enhanced fallback based on user message (only if API fails)
        if not bot_reply:
            if user_message.lower() == "hello":
                bot_reply = "Hi! I'm Qyra, your travel assistant. Try 'book _flight' or 'how can i book hotel'!"
            elif user_message.lower() == "book_flight":
                bot_reply = "Flights: 1) DEL to BOM - $200, 2) DEL to BLR -  $250. Please provide more details to proceed!"
            elif user_message.lower() == "how can i book hotel":
                bot_reply = "To book a hotel, visit a site like Expedia or contact a travel agent. Let me know your location for options!"
            else:
                bot_reply = f"Sorry, I couldn’t process '{user_message}' with the model. Try 'book_flight' or 'how can i book hotel'!"
        logger.info(f"Final response: {bot_reply}")

        # Save message if authenticated
        if request.user.is_authenticated:
            UserMessage.objects.create(user=request.user, message=user_message, response=bot_reply)
            logger.info(f"Message saved for user {request.user.username}: {user_message}")

        return JsonResponse({"reply": bot_reply})

    except requests.exceptions.RequestException as e:
        logger.error(f"OpenRouter API error: {str(e)}")
        return JsonResponse({"reply": "Error communicating with OpenRouter. Fallback: Hello from Qyra!"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_ai: {str(e)}")
        return JsonResponse({"reply": "Something went wrong. Fallback: Hello from Qyra!"}, status=500)



    
@login_required
def chatbot_page(request):
    chat_history = UserMessage.objects.filter(user=request.user).order_by("timestamp")
    return render(request, "chat.html", {
        "chat_history": chat_history,
    })


def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            logger.info(f"User logged in: {form.get_user().username}")
            return redirect('chatbot_page')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

# --- Django REST Framework API Views ---

from django.utils import timezone
import json
import logging

# Activate the timezone at module load
timezone.activate(timezone.get_current_timezone())

logger = logging.getLogger(__name__)

@csrf_exempt
def test_api(request):
    if request.method != "POST":
        logger.warning(f"Invalid method {request.method} for test_api")
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        current_time = timezone.localtime(timezone.now())
        logger.info(f"Test API called with message: {user_message} at {current_time}")

        if not user_message:
            logger.warning("Empty message received in test_api")
            return JsonResponse({"reply": "Please provide a message for testing."})

        # Simulate different test scenarios based on message
        response = {"reply": "", "buttons": [], "custom": None}
        
        if user_message.lower() == "test_hotels":
            # Fetch real hotels from the database
            hotels = Hotel.objects.all()[:2]  # Limit to 2 for testing
            serializer = HotelSerializer(hotels, many=True, context={'request': request})
            cards = [
                {
                    "image": hotel["image"] or "/media/hotel_images/manali.webp",
                    "title": hotel["name"],
                    "subtitle": hotel["location"],
                    "rating": str(hotel["rating"]),
                    "price": str(hotel["price_per_night"]),
                    "amenities": hotel["amenities"],
                    "buttons": [{"title": "Book Now", "payload": f'book_hotel{{"hotel_name": "{hotel["name"]}"}}'}]
                } for hotel in serializer.data
            ]
            response.update({
                "reply": f"Found {len(cards)} hotels for testing.",
                "custom": {"type": "hotel_cards", "cards": cards}
            })

        elif user_message.lower() == "test_packages":
            # Fetch travel packages
            packages = TravelPackage.objects.all()[:2]
            serializer = TravelPackageSerializer(packages, many=True)
            response["reply"] = "Available travel packages:"
            response["buttons"] = [
                {
                    "title": pkg["name"],
                    "payload": f'/package_detail{{"package_name":"{pkg["name"]}"}}'
                } for pkg in serializer.data
            ]

        elif user_message.lower() == "test_rasa":
            # Test Rasa integration
            sender_id = request.user.username if request.user.is_authenticated else "anonymous"
            rasa_response = requests.post(
                "http://localhost:5005/webhooks/rest/webhook",
                json={"sender": sender_id, "message": "hello"},
                timeout=30
            )
            rasa_response.raise_for_status()
            messages = rasa_response.json()
            bot_reply = " ".join([msg.get("text", "") for msg in messages]).strip() or \
                        "Rasa responded, but no text was returned."
            response["reply"] = f"Rasa test response: {bot_reply}"
            response["buttons"] = [
                {"title": "Test Rasa Again", "payload": "test_rasa"},
                {"title": "Back to Chat", "payload": "/start"}
            ]

        else:
            # Default response for generic testing
            response["reply"] = f"Test API received: {user_message} at {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
            response["buttons"] = [
                {"title": "Test Hotels", "payload": "test_hotels"},
                {"title": "Test Packages", "payload": "test_packages"},
                {"title": "Test Rasa", "payload": "test_rasa"}
            ]

        return JsonResponse(response)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in test_api request: {str(e)}")
        return JsonResponse({"reply": "Invalid JSON format."}, status=400)
    except requests.exceptions.RequestException as e:
        logger.error(f"Rasa server error in test_api: {str(e)}")
        return JsonResponse({"reply": "Error communicating with Rasa server."}, status=500)
    except Exception as e:
        logger.error(f"Test API error: {str(e)}")
        return JsonResponse({"reply": "Error in test API."}, status=500)

class TravelPackageListAPIView(APIView):
    """API view for listing travel packages."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        packages = TravelPackage.objects.all()
        serializer = TravelPackageSerializer(packages, many=True)
        return Response(serializer.data)

class HotelListAPIView(generics.ListAPIView):
    """API view for listing hotels, optionally filtered by location."""
    serializer_class = HotelSerializer

    def get_queryset(self):
        queryset = Hotel.objects.all()
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location.strip())
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class FlightListAPIView(APIView):
    """API view for listing all flights."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        flights = Flight.objects.all()
        serializer = FlightSerializer(flights, many=True)
        return Response(serializer.data)

class BookingListAPIView(APIView):
    """API view for listing all bookings."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

class UserMessageListAPIView(APIView):
    """API view for listing all user messages."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        messages = UserMessage.objects.all()
        serializer = UserMessageSerializer(messages, many=True)
        return Response(serializer.data)

from .serializers import CombinedUserSerializer
from rest_framework.permissions import IsAuthenticated

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = CombinedUserSerializer(user, context={'request': request})
        return Response(serializer.data)