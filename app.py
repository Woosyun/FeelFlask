import streamlit as st
from streamlit_lottie import st_lottie
from session_mangement import initialize_session_state, load_lottie_files, load_lottiefile
from page_handler import *
import json
import numpy as np


# Load Lottie animations
welcome_animations = load_lottie_files("lottie_files/welcome ({}).json", 1, 10)
loading_animations = load_lottie_files("lottie_files/loading ({}).json", 1, 10)
cocktail_animations = load_lottie_files("lottie_files/cocktail ({}).json", 1, 41)

with open('./flavor_update.json', 'r') as fr:
    flavor_info = json.load(fr)

# Initialize session state
initialize_session_state()

# Main app logic
if st.session_state.page == 0:
    handle_welcome_page(welcome_animations)
elif st.session_state.page == 1:
    handle_drink_type_page()
elif st.session_state.page == 2:
    handle_input_by_images(st.session_state.drink_type)
elif st.session_state.page == 3:
    handle_input_seed_ingredient(loading_animations)
elif st.session_state.page == 4:
    show_loading_page()
elif st.session_state.page == 5:
    if 'prediction_result' in st.session_state:
        show_recommendation(st.session_state.prediction_result,
                            cocktail_animations)
# elif st.session_state.page == 9:
    # handle_feedback_page()

# def push_data(inputs, pred_ingredients, pred_amounts, feedback):