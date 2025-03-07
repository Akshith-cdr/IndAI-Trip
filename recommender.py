import streamlit as st
import requests
import geocoder
import math
import pandas as pd
import folium
from streamlit_folium import folium_static

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

# Streamlit App UI
st.set_page_config(page_title="Nearby Places Finder", layout="wide")

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