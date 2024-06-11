import streamlit as st
import json
import numpy as np

def initialize_session_state():
    # 페이지 업데이트 구분용
    if 'page' not in st.session_state:
        st.session_state.page = 0
    # Alcoholi / Non-Alcoholic 인지 정보를 저장하기 위한 변수
    if 'drink_type' not in st.session_state:
        st.session_state.drink_type = None
    # User Profile(15가지 변수)의 정보를 저장하고 업데이트 하기 위한 변수
    if 'main_feature_values' not in st.session_state:
        st.session_state.main_feature_values = None
    # 모델 inference 후에 결과를 저장하기 위한 변수
    if 'predict_result' not in st.session_state:
        st.session_state.predict_result = None
    # feature 이름을 입력시에 index 값을 반환하는 변수
    if 'feature_to_index' not in st.session_state:
        st.session_state.feature_to_index = None
    # img이름을 입력시에 index 값을 반환하는 변수
    if 'img_to_idx' not in st.session_state:
        st.session_state.img_to_idx = None
    # image path를 저장하는 변수. img_to_idx와 같이 사용하면 인덱스에 맞게 경로에 접근할 수 있음
    if 'img_path_list' not in st.session_state:
        st.session_state.img_path_list = None
    # 선택된 특성을 저장하는 변수
    if 'choice' not in st.session_state:
        st.session_state.choice = {}
        ingredient_list = ['lemon', 'bonfire', 'chocolate', 'mint', 'almond', 'lime', 'milk', 'pretzel',
                           'dark_chocolate', 'lavender', 'grapefruit', 'pepper', 'basil', 'pistachio', 'cola', 
                           'honey', 'ice_cream', 'salt', 'champagne', 'candy', 'hot_pepper', 'coffee_beans',
                           'rose']
        for ingredient in ingredient_list:
            st.session_state.choice[ingredient] = 0 # must be intialized as 0
    # loading animation을 미리 loading page 전 페이지에 선택하고 사용하기 위한 변수
    if 'loading_animation' not in st.session_state:
        st.session_state.loading_animation = None
    # feedback_rating값을 저장합니다. 해당 값은 app.py의 connection을 통해 google sheet에 저장됩니다.
    if 'feedback_ratings' not in st.session_state:
        st.session_state.feedback_ratings = 0
    if 'is_submit' not in st.session_state:
        st.session_state.is_submit = False
    # 선택된 재료에 대한 특성을 저장하는데 사용하는 변수입니다. 특성은 'sweet', 'sour', 'bitter', 'fruity', 'umami',
    # 'smoky', 'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty' 입니다.
    if 'choice_state' not in st.session_state:
        st.session_state.choice_state = np.array([50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50])


def load_lottie_files(pattern, start, end):
    files = []
    for i in range(start, end + 1):
        files.append(load_lottiefile(pattern.format(i)))
    return files

def load_lottiefile(filepath):
    with open(filepath, "r") as f:
        return json.load(f)
