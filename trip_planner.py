import streamlit as st
import google.generativeai as genai

# Set up Gemini API key
API_KEY = "AIzaSyCvYPF4FLCXw07_ebw63Z_WKOVhx1f8dT0"  # Replace with your actual Gemini API key
genai.configure(api_key=API_KEY)

# Streamlit app title
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