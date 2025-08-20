import os
import sys
import django
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

# Setup Django environment for accessing models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mysite'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

from chatbot.models import UserMessage, TravelPackage, HotelBooking, FlightBooking, Booking

from django.contrib.auth.models import User
import requests
from rasa_sdk.events import SlotSet
from rasa_sdk.forms import FormValidationAction
from datetime import datetime
from typing import Any, Text, Dict, List
from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType


class ValidateHotelBookingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_hotel_booking_form"

    def validate_check_in_date(self, slot_value: Any, dispatcher: CollectingDispatcher,
                           tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            datetime.strptime(slot_value, "%Y-%m-%d")
            return {"check_in_date": slot_value}
        except ValueError:
            dispatcher.utter_message(text="⚠️ Please enter the check-in date in YYYY-MM-DD format.")
            return {"check_in_date": None}

    def validate_nights(self, slot_value: Any, dispatcher: CollectingDispatcher,
                        tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            nights = int("".join(filter(str.isdigit, str(slot_value))))
            if nights > 0:
                return {"nights": nights}
        except:
            pass
        dispatcher.utter_message(text="Please provide a valid number of nights.")
        return {"nights": None}

    def validate_guests(self, slot_value: Any, dispatcher: CollectingDispatcher,
                        tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            guests = int("".join(filter(str.isdigit, str(slot_value))))
            if guests > 0:
                return {"guests": guests}
        except:
            pass
        dispatcher.utter_message(text="Please provide a valid number of guests.")
        return {"guests": None}


class ActionSubmitHotelBooking(Action):
    def name(self) -> Text:
        return "action_submit_hotel_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:
        user_id = tracker.sender_id
        hotel = tracker.get_slot("hotel_name")
        date = tracker.get_slot("check_in_date")
        guests = tracker.get_slot("guests")
        nights = tracker.get_slot("nights")

        if not all([hotel, date, guests, nights]):
            dispatcher.utter_message(text="⚠️ Booking could not be completed. Missing information.")
            return []

        try:
            user = User.objects.get(username=user_id)
            hotel_booking = HotelBooking.objects.create(
                user=user,
                hotel_name=hotel,
                check_in_date=date,
                guests=guests,
                nights=nights
            )

            # Create a Booking entry linked to HotelBooking
            Booking.objects.create(
                user=user,
                booking_type="hotel",
                reference_id=f"Hotel:{hotel_booking.id}"
            )

            dispatcher.utter_message(
                text=f"✅ Booking confirmed at *{hotel}* from *{date}* for *{nights}* nights with *{guests}* guests."
            )
        except User.DoesNotExist:
            dispatcher.utter_message(text="⚠️ Booking failed. User not found.")
        return []


# ---------------------- FLIGHT BOOKING ----------------------

class ValidateFlightBookingForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_flight_booking_form"

    def validate_travel_date(self, slot_value: Any, dispatcher: CollectingDispatcher,
                             tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        try:
            datetime.strptime(slot_value, "%Y-%m-%d")
            return {"travel_date": slot_value}
        except ValueError:
            dispatcher.utter_message(text="Please provide a valid date in YYYY-MM-DD format.")
            return {"travel_date": None}

    def validate_departure(self, slot_value: Any, dispatcher: CollectingDispatcher,
                           tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if slot_value:
            return {"departure": slot_value}
        dispatcher.utter_message(text="Please enter departure city.")
        return {"departure": None}

    def validate_destination(self, slot_value: Any, dispatcher: CollectingDispatcher,
                             tracker: Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]:
        if slot_value:
            return {"destination": slot_value}
        dispatcher.utter_message(text="Please enter destination city.")
        return {"destination": None}


class ActionSubmitFlightBooking(Action):
    def name(self) -> Text:
        return "action_submit_flight_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:
        user_id = tracker.sender_id
        from_city = tracker.get_slot("departure")
        to_city = tracker.get_slot("destination")
        travel_date = tracker.get_slot("travel_date")

        if not all([from_city, to_city, travel_date]):
            dispatcher.utter_message(text="⚠️ Flight booking failed. Missing departure, destination, or date.")
            return []

        try:
            user = User.objects.get(username=user_id)
            flight_booking = FlightBooking.objects.create(
                user=user,
                departure=from_city,
                destination=to_city,
                travel_date=travel_date
            )

            # Create a Booking entry linked to FlightBooking
            Booking.objects.create(
                user=user,
                booking_type="flight",
                reference_id=f"Flight:{flight_booking.id}"
            )

            dispatcher.utter_message(
                text=f"✅ Flight booked from *{from_city}* to *{to_city}* on *{travel_date}*."
            )
        except User.DoesNotExist:
            dispatcher.utter_message(text="⚠️ Booking failed. User not found.")
        return []


from urllib.parse import quote
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import requests

class ActionShowHotelsByLocation(Action):
    def name(self) -> Text:
        return "action_show_hotels_by_location"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        location = tracker.get_slot("location")

        if not location:
            dispatcher.utter_message(text="Please provide a location to search for hotels.")
            return []

        try:
            encoded_location = quote(location)
            url = f"http://localhost:8000/api/hotels/?location={encoded_location}"
            response = requests.get(url)

            if response.status_code == 200:
                hotels = response.json()

                if isinstance(hotels, list) and len(hotels) > 0:
                    cards = []
                    for hotel in hotels:
                        image_path = hotel.get("image")
                        if image_path:
                            image_url = f"http://localhost:8000/media/{image_path}"
                        else:
                            image_url = "http://localhost:8000/media/hotel_images/default.webp"

                        card = {
                            "image": image_url,
                            "title": hotel["name"],
                            "subtitle": hotel["location"],
                            "rating": str(hotel["rating"]),
                            "price": str(hotel["price_per_night"]),
                            "amenities": hotel["amenities"],
                            "buttons": [
                                {
                                    "title": "Book Now",
                                    "payload": f'/book_hotel{{"hotel_name": "{hotel["name"]}"}}'
                                }
                            ]
                        }
                        cards.append(card)

                    dispatcher.utter_message(custom={
                        "type": "hotel_cards",
                        "cards": cards
                    })
                else:
                    dispatcher.utter_message(text=f"Sorry, no hotels found in {location}.")
            else:
                dispatcher.utter_message(text="Failed to fetch hotel data. Please try again later.")

        except Exception as e:
            dispatcher.utter_message(text=f"Error while searching for hotels: {e}")

        return []



class ActionShowTravelPackages(Action):
    def name(self) -> Text:
        return "action_show_travel_packages"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        packages = TravelPackage.objects.all()
        if not packages:
            dispatcher.utter_message(text="Sorry, no travel packages are currently available.")
            return []

        message = "Here are some available travel packages:\n"
        for p in packages:
            message += f"- {p.name} in {p.destination} for {p.duration_days} days at ₹{p.price}\n"

        dispatcher.utter_message(text=message)
        return []


class ActionShowCategories(Action):
    def name(self) -> Text:
        return "action_show_categories"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        buttons = [
            {"title": "🏖️ Beach Holidays", "payload": '/show_destinations{"category":"beach"}'},
            {"title": "⛰️ Mountain Adventures", "payload": '/show_destinations{"category":"mountain"}'},
            {"title": "🏙️ City Tours", "payload": '/show_destinations{"category":"city"}'},
        ]
        dispatcher.utter_message(text="Choose a travel category:", buttons=buttons)
        return []


class ActionShowDestinations(Action):
    def name(self) -> Text:
        return "action_show_destinations"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        category = tracker.get_slot("category")

        if not category:
            dispatcher.utter_message(text="Please specify a category (beach, mountain, city).")
            return []

        packages = TravelPackage.objects.filter(category__iexact=category)
        if not packages:
            dispatcher.utter_message(text=f"Sorry, we couldn't find any packages in the {category} category.")
            return []

        buttons = []
        for pkg in packages:
            buttons.append({
                "title": pkg.destination,
                "payload": f'/package_detail{{"package_name":"{pkg.name}"}}'
            })

        dispatcher.utter_message(text=f"Here are the {category} destinations available:", buttons=buttons)
        return []


class ActionPackageDetail(Action):
    def name(self) -> Text:
        return "action_package_detail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        package_name = tracker.get_slot("package_name")

        if not package_name:
            dispatcher.utter_message(text="Please specify which travel package you're interested in.")
            return []

        try:
            travel_package = TravelPackage.objects.get(name__iexact=package_name)
            response = (
                f"📦 *{travel_package.name}*\n"
                f"📍 Destination: {travel_package.destination}\n"
                f"🗒️ {travel_package.description}\n"
                f"💰 Price: ₹{travel_package.price}\n"
                f"⏱️ Duration: {travel_package.duration_days} days"
            )
            buttons = [
                {"title": "Book a Flight", "payload": "/book_flight"},
                {"title": "Search Hotels", "payload": f'/search_hotels{{"location": "{travel_package.destination}"}}'},
                {"title": "Back to Packages", "payload": "/travel_packages"}
            ]
            # Set location slot to package destination for downstream hotel search
            dispatcher.utter_message(text=response, buttons=buttons)
            return [
                SlotSet("location", travel_package.destination),
                SlotSet("package_name", travel_package.name),
            ]
        except TravelPackage.DoesNotExist:
            response = f"Sorry, I couldn’t find a travel package named '{package_name}'."
            buttons = [
                {"title": "Back to Packages", "payload": "/travel_packages"}
            ]

        dispatcher.utter_message(text=response, buttons=buttons)
        return []

class ActionCancelBooking(Action):
    def name(self) -> Text:
        return "action_cancel_booking"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Here, implement your logic for booking cancellation
        dispatcher.utter_message(text="Your booking cancellation request has been received and is being processed.")
        return []


class ActionSaveMessage(Action):
    def name(self) -> Text:
        return "action_save_message"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_input = tracker.latest_message.get("text", "")
        bot_response = next(
            (e.get("text") for e in reversed(tracker.events)
             if e.get("event") == "bot" and e.get("text")), 
            "No response"
        )
        sender_id = tracker.sender_id

        try:
            user = User.objects.get(username=sender_id)
            UserMessage.objects.create(user=user, message=user_input, response=bot_response)
            print(f"Saved message for user {sender_id}")
        except User.DoesNotExist:
            print(f"[Warning] User '{sender_id}' not found. Message not saved.")
        except Exception as e:
            print(f"[Error] Failed to save message: {e}")

        return []