import google.generativeai as genai
import os
import streamlit as st

from dotenv import load_dotenv
from time import sleep

# Load API Key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-pro")

# Streamlit UI
st.set_page_config(
    page_title="Geo Guide Chatbot",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="collapsed"
)

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