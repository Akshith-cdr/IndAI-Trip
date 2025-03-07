import streamlit as st
import google.generativeai as genai
import requests
import geocoder
import math
import pandas as pd
import folium
from streamlit_folium import folium_static
from PIL import Image
import os
from dotenv import load_dotenv
from time import sleep

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHERSTACK_API_KEY = "a2691665eb799c4363aad16a040c1cb0"

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-pro")

# Streamlit App UI
st.set_page_config(page_title="Geo Guide Agent", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .stTextInput input {
        border-radius: 20px;
        padding: 12px;
        border: 2px solid #4CAF50 !important;
    }
    .stTextInput input:focus {
        border-color: #45a049 !important;
        box-shadow: 0 0 0 2px #45a04933;
    }
    .stButton button {
        border-radius: 20px;
        background-color: #4CAF50;
        color: white;
        padding: 12px 24px;
        border: none;
        cursor: pointer;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #45a049;
        transform: scale(1.05);
    }
    .chat-message {
        padding: 15px 20px;
        border-radius: 20px;
        margin: 12px 0;
        max-width: 80%;
        word-wrap: break-word;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #4CAF50;
        color: white;
        margin-left: auto;
        margin-right: 0;
    }
    .bot-message {
        background-color: #f8f9fa;
        color: #333;
        margin-left: 0;
        margin-right: auto;
        border: 1px solid #dee2e6;
    }
    .main-container {
        padding-bottom: 100px;
    }
    .input-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 20px;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        z-index: 100;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("🌍 Geo Guide Agent")
st.write("Your personal travel assistant - Explore destinations, plan trips, and get real-time recommendations!")

# Function to get the user's location (latitude, longitude)
def get_location():
    """Fetch user's live location (latitude, longitude)."""
    g = geocoder.ip('me')  # Get location from IP
    if g.latlng:
        st.write(f"📍 **Your location:** Latitude: {g.latlng[0]}, Longitude: {g.latlng[1]}")
        return g.latlng
    else:
        st.warning("Failed to fetch your location. Using default location (Delhi, India).")
        return [28.6139, 77.2090]  # Default location (Delhi, India)

# Haversine formula to calculate distance between two points (lat, lon) in meters
def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi, delta_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distance in meters

# Function to fetch nearby places using Overpass API
def get_nearby_places(lat, lon, radius):
    """Fetch places using Overpass API with a dynamic radius."""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"](around:{radius},{lat},{lon});
      node["shop"](around:{radius},{lat},{lon});
      node["tourism"](around:{radius},{lat},{lon});
    );
    out body;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    if response.status_code == 200:
        return response.json().get('elements', [])
    else:
        st.error(f"Overpass API Error: {response.status_code}")
        return []

# Function to get recommendations dynamically
def get_recommendations():
    """Fetch recommendations with dynamic radius adjustment."""
    location = get_location()
    if not location:
        return None, "Error: Failed to fetch user location"

    lat, lon = location
    radius = 5000  # Start with a 5 km radius
    places = get_nearby_places(lat, lon, radius)

    # Dynamically increase radius if needed
    while len(places) < 3 and radius <= 20000:
        radius += 5000  # Increase by 5 km
        places = get_nearby_places(lat, lon, radius)

    if not places:
        return None, "No places found nearby"

    recommendations = []
    for place in places:
        place_lat, place_lon = place.get("lat"), place.get("lon")
        distance_meters = haversine(lat, lon, place_lat, place_lon)  # Calculate distance

        # Convert distance to readable format
        distance_display = f"{int(distance_meters)} meters" if distance_meters < 1000 else f"{int(distance_meters / 1000)} km"

        recommendations.append({
            "name": place.get("tags", {}).get("name", "Unnamed"),
            "type": place.get("tags", {}).get("amenity", place.get("tags", {}).get("shop", place.get("tags", {}).get("tourism", "Unknown"))),
            "latitude": place_lat,
            "longitude": place_lon,
            "distance": distance_display,
            "address": place.get("tags", {}).get("addr:street", "Unknown Address"),
            "details": place.get("tags", {}).get("opening_hours", "No data available")
        })
    
    # Sort recommendations by distance
    recommendations.sort(key=lambda x: float(x["distance"].split()[0]))
    return recommendations, None

# Function to get weather information
def get_weather(lat, lon):
    """Fetch weather information using Weatherstack API."""
    url = f"http://api.weatherstack.com/current?access_key={WEATHERSTACK_API_KEY}&query={lat},{lon}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Weatherstack API Error: {response.status_code}")
        return None

# Streamlit App UI
st.title("📍 Nearby Places Recommendation System")
st.write("This app dynamically fetches and displays places near your location.")

# Fetch Recommendations
with st.spinner("Fetching nearby places..."):
    places, error = get_recommendations()

if error:
    st.error(error)
else:
    # Display results in a table
    st.subheader("📋 Nearby Places")
    df = pd.DataFrame(places)
    st.dataframe(df[["name", "type", "distance", "address", "details"]])

    # Show map with locations
    st.subheader("🗺️ Map View")
    user_location = get_location()
    if user_location:
        map_center = user_location
        m = folium.Map(location=map_center, zoom_start=14)

        # Add user marker
        folium.Marker(
            location=user_location,
            popup="You are here",
            icon=folium.Icon(color="blue")
        ).add_to(m)

        # Add place markers
        for place in places:
            folium.Marker(
                location=[place["latitude"], place["longitude"]],
                popup=f"{place['name']} ({place['type']})\n{place['distance']}",
                icon=folium.Icon(color="red")
            ).add_to(m)

        folium_static(m)

# Weather Button
if st.button("Get Weather"):
    user_location = get_location()
    if user_location:
        weather_data = get_weather(user_location[0], user_location[1])
        if weather_data:
            st.write(f"**Temperature:** {weather_data['current']['temperature']}°C")
            st.write(f"**Weather:** {weather_data['current']['weather_descriptions'][0]}")
            st.write(f"**Humidity:** {weather_data['current']['humidity']}%")
            st.write(f"**Wind Speed:** {weather_data['current']['wind_speed']} km/h")

# SOS Button
if st.button("🚨 SOS"):
    st.write("Emergency SOS activated. Help is on the way!")

# Add Photos as Memories
uploaded_file = st.file_uploader("Add a photo as a memory", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Your Memory", use_column_width=True)

# AI Trip Planner
st.title("AI Trip Planner 🌍")
st.write("Welcome to the AI Trip Planner! Enter your trip details below.")

# Collect user inputs using Streamlit widgets
start_date = st.text_input("Enter the start date (YYYY-MM-DD):")
end_date = st.text_input("Enter the end date (YYYY-MM-DD):")
start_place = st.text_input("Enter the starting place:")
destination = st.text_input("Enter the destination:")
budget = st.text_input("Enter your budget (e.g., $1000):")
special_activities = st.text_input("Any special activities you want to include? (e.g., hiking, museums):")

# Button to generate itinerary
if st.button("Generate Itinerary"):
    if not all([start_date, end_date, start_place, destination, budget, special_activities]):
        st.error("Please fill in all the fields!")
    else:
        with st.spinner("Generating your itinerary..."):
            try:
                # Initialize the model with 'gemini-2.0-flash'
                model = genai.GenerativeModel('gemini-2.0-flash')

                # Create a detailed prompt for the AI
                prompt = f"""
                Create a detailed day-by-day travel itinerary for a trip from {start_place} to {destination}.
                - Start Date: {start_date}
                - End Date: {end_date}
                - Budget: {budget}
                - Special Activities: {special_activities}
                Include activities, transportation, accommodation, and food recommendations.
                Format the itinerary clearly with day-wise breakdowns.
                """

                # Generate the itinerary using Gemini AI
                response = model.generate_content(prompt)
                itinerary = response.text

                # Display the itinerary
                st.success("Your AI-Generated Itinerary:")
                st.write(itinerary)

                # Option to download the itinerary as a text file
                st.download_button(
                    label="Download Itinerary",
                    data=itinerary,
                    file_name="itinerary.txt",
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"Error generating itinerary: {e}")

# Chatbot
st.title("🌍 IndAI Bot")
st.markdown("""
    <div style='text-align: center; margin-bottom: 30px; color: #666;'>
        Your personal travel assistant - Ask about destinations, itineraries, or travel tips!
    </div>
    """, unsafe_allow_html=True)

# Store chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to check if the input is travel-related
def is_travel_related(prompt):
    travel_keywords = [
       "travel", "trip", "itinerary", "distance", "destination", "flight", "hotel", "tour", "guide", "geo",
        "far", "restaurant", "go", "going", "visit", "explore", "resort", "time", "camping", "vacation",
        "excertion", "location", "roam", "hostel", "sight", "place", "nature", "history", "historical",
        "public transport", "accommodation", "hiking", "safari", "dinner", "snacks", "budget", "safety",
        "customs", "weather", "restrictions", "information", "culture", "museum", "luxury", "car", "train",
        "packing", "backpack", "currency", "insurance", "festival", "concert", "street food", "lodge",
        "lodging", "landmark", "adventure", "country", "mountains", "beach", "metro", "cab", "ride", "ferry",
        "cruise", "island", "park", "parking", "ambulance", "police", "airplane", "airport", "railway", "bus",
        "map", "gps", "subway", "pub", "bar", "beverages", "nightlife", "night", "cost", "living", "state",
        "district", "local", "urban", "rural", "nation", "energy", "shopping", "market", "share", "prize",
        "rupees", "dollars", "india", "ai", "cuisine"

    ]
    return any(keyword in prompt.lower() for keyword in travel_keywords)

# Function to get response from Gemini
def get_response(prompt):
    if is_travel_related(prompt):
        with st.spinner("🌍 Scanning the globe..."):
            sleep(0.5)  # Simulate processing time
            response = model.generate_content(prompt)
            return response.text
    else:
        return "I specialize in travel-related queries! Ask me about destinations, trips, or travel planning."

# Fixed input footer at the top
with st.form(key="chat_input", clear_on_submit=True):
    input_col, btn_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            "Ask me anything about travel...",
            placeholder="Where would you like to go today?",
            key="input",
            label_visibility="collapsed"
        )
    with btn_col:
        submit_button = st.form_submit_button("Send →")

# Handle user input
if submit_button and user_input:
    # Store user input
    st.session_state.chat_history.append({"role": "user", "text": user_input})

    # Get and store bot response
    bot_response = get_response(user_input)
    st.session_state.chat_history.append({"role": "bot", "text": bot_response})

    # Refresh to show updates
    st.rerun()

# Main chat container
main_container = st.container()

# Display chat history in reverse order
with main_container:
    for message in reversed(st.session_state.chat_history):
        if message["role"] == "user":
            st.markdown(f"""
                <div class="chat-message user-message">
                    👤 <strong>You:</strong> {message['text']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="chat-message bot-message">
                    🤖 <strong>Geo Guide:</strong> {message['text']}
                </div>
                """, unsafe_allow_html=True)

# Clear chat button (floating at bottom right)
st.markdown("""
    <div style="position: fixed; bottom: 25px; right: 25px; z-index: 101;">
        <button onclick="window.location.reload()" 
                style="background: #ff4444; color: white; border: none; 
                       padding: 8px 16px; border-radius: 15px; cursor: pointer;
                       transition: all 0.3s ease;">
            Clear Chat 🗑️
        </button>
    </div>
    """, unsafe_allow_html=True)