"""
Basic python code example for Real-time Aircraft notifications within
a specified radius and altitude range. (overhead traffic notification basics)


This script retrieves information about aircraft from a local flight tracker
(PiAware with FlightAware Pro Stick)
and calculates the distance between the plane's coordinates and a set of home
coordinates. If the plane is within X miles of the home coordinates and at an
altitude of Z feet or lower, the flight information is printed to console.
(Later this will be saved to database...) 
"""

import requests
from geopy.distance import geodesic
import time
from datetime import datetime, timedelta
from urllib.parse import quote

# Home-coordinates
home_coords = (40, 10)

# Log all planes within MaxDistance and MinHeight
MaxDistance = 7  # Km
MaxHeight = 35000  # Foot

# URL for the local FlightAware PiAware info
url = "http://127.0.0.1:8755/data/aircraft.json"

# Initialize a dictionary for tracking notified aircraft with timestamps
notified_aircraft = {}
notification_window = timedelta(minutes=10)  # Notification window of 10 minutes

while True:
    try:
        # Current time
        now = datetime.now()

        # Remove aircraft notified more than 10 minutes ago
        notified_aircraft = {
            flight: timestamp
            for flight, timestamp in notified_aircraft.items()
            if now - timestamp <= notification_window
        }

        # Get the JSON data from the URL
        response = requests.get(url)
        data = response.json()

        # Loop through all aircraft in the JSON data
        for aircraft in data['aircraft']:
            flight = aircraft.get('flight')
            if flight is None:
                flight = "Unavailable"
            lat = aircraft.get('lat')
            lon = aircraft.get('lon')
            alt = aircraft.get('alt_baro')

            # Verify coordinates are valid
            if lat is None or lon is None:
                continue

            # Calculate the distance from home coordinates to the plane's coordinates
            plane_coords = (lat, lon)
            distance = geodesic(home_coords, plane_coords).km

            # If the plane meets criteria and hasn't been notified recently
            if distance <= MaxDistance and alt <= MaxHeight:
                if flight not in notified_aircraft:
                    # Add the flight to the dictionary with the current timestamp
                    notified_aircraft[flight] = now

                    # Generate FlightAware link if flight code is available
                    if flight != "Unavailable":
                        flightaware_link = f"https://www.flightaware.com/live/flight/{flight}"
                    else:
                        flightaware_link = "N/A"

                    # Prepare the Markdown-formatted message
                    data = (
                        f"✈️ *New plane spotted:*\n\n"  # Added the airplane emoji
                        f"*Flight:* [{flight}]({flightaware_link})\n"
                        f"*Distance:* {distance:.2f} km\n"
                        f"*Altitude:* {alt} ft\n"
                        f"*Latitude:* {lat}\n"
                        f"*Longitude:* {lon}"
                    )

                    # Print to console
                    print(
                        f"{now.strftime('%Y-%m-%d %H:%M:%S')} | Flight {flight} | Distance: {distance:.2f} km "
                        f"| Altitude: {alt} ft | Latitude: {lat} | Longitude: {lon} "
                        f"| FlightAware: {flightaware_link}"
                    )

                    # Send to Telegram with Markdown parsing
                    requests.post(
                        'https://api.telegram.org/bot/sendMessage',
                        json={
                            "chat_id": "",
                            "text": data,
                            "parse_mode": "Markdown"
                        }
                    )
    except Exception as e:
        print("Error:", e)

    time.sleep(5)

