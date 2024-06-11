import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import requests
import random
import time
from PIL import Image
import base64
from pathlib import Path
import json
from streamlit_lottie import st_lottie
from streamlit_star_rating import st_star_rating

def restart_btn():
    col1, col2, col3 = st.columns([50, 14, 50])
    with col2:
        if st.button("Restart", key="restart", type='secondary'):
            initialize_state()
            st.rerun()

def update_feature(feature_dic, select_feature, value_list):
    for i, feature in enumerate(select_feature):
        feature_dic[feature] += value_list[i] # 값 업데이트
    return feature_dic

def img_to_bytes(img_path):
    img_bytes = Path(img_path).read_bytes()
    encoded = base64.b64encode(img_bytes).decode()
    return encoded
def img_to_html(img_path):
    img_html=f"""
    <img src='data:image/png;base64,{img_to_bytes(img_path)}' class='img-fluid' style='max-width: 100%;max-height: 100%;'>
    """
    return img_html

def filter_feature(feature_dic):
    for key in feature_dic.keys():
        if key != "seed":
            feature_dic[key] = float(feature_dic[key])
            if feature_dic[key] > 100:
                feature_dic[key] = float(100)
            elif feature_dic[key] < 0:
                feature_dic[key] = float(0)
    print("Filtered Feature: ", feature_dic)
    return feature_dic


# restart 한다면 session_state를 다시 초기화 시켜 주어야 합니다.
# 그래야 기존의 정보가 남아있지 않고, 초기화된 정보로 시작할 수 있습니다.
def initialize_state():
    st.session_state.page = 0
    st.session_state.drink_type = None
    st.session_state.main_feature_values = None
    st.session_state.predict_result = None
    st.session_state.feature_to_index = None
    st.session_state.img_to_idx = None
    st.session_state.img_path_list = None
    st.session_state.choice = {}
    ingredient_list = ['lemon', 'bonfire', 'chocolate', 'mint', 'almond', 'lime', 'milk', 'pretzel',
                        'dark_chocolate', 'lavender', 'grapefruit', 'pepper', 'basil', 'pistachio', 'cola', 
                        'honey', 'ice_cream', 'salt', 'champagne', 'candy', 'hot_pepper', 'coffee_beans',
                        'rose']
    for ingredient in ingredient_list:
        st.session_state.choice[ingredient] = 0 # must be intialized as 0
    st.session_state.loading_animation = None
    st.session_state.feedback_ratings = 0
    st.session_state.is_submit = False
    st.session_state.selected_ingredient = ""
    st.session_state.selected_index = -1
    st.session_state.choice_state = np.array([50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50])


# 다음 페이지로 넘어가는 함수
# st.session_state.page 값을 1 증가시키고, st.rerun()을 통해 다음 페이지로 넘어갑니다. (순서는 app.py 참고)
def next_page():
    st.session_state.page += 1
    st.rerun()

# 처음 시작 페이지를 보여주는 함수
# st.markdown을 이용하여 <h1></h1>, <p></p> 태그를 이용하여 글자를 보여줍니다.
def handle_welcome_page(welcome_animations):
    welcome_animation = random.choice(welcome_animations)
    st_lottie(welcome_animation, height=300, key="welcome_animation")

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Welcome to the Cocktail Recommender System</h1>
            <p>Discover your perfect cocktail based on your personal preferences!</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Center the button using columns
    col1, col2, col3 = st.columns([5, 3, 5])
    with col2:
        if st.button("Start Your Journey", key="start", type='primary'):
            next_page()

# Alcoholic인지, Non-Alcoholic인지 선택하는 페이지를 보여주는 함수
# Alcoholic이라면, ABV값을 따로 입력받고 Non-Alcoholic이라면 ABV=0으로 설정합니다.
def handle_drink_type_page():
    # CSS 스타일링 추가
    st.markdown("""
    <style>
    .element-container:has(#alcoholic_button_span) + div button {
        background-color: #ffb6c1; /* 파스텔 핑크 */
        color: white;
        font-size: 50;
        padding: 20px;
        border: none;
        border-radius: 50px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
        width: 300px;
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .element-container:has(#alcoholic_button_span) + div button:hover {
        background-color: #ff99aa;
    }
    .element-container:has(#non_alcoholic_button_span) + div button {
        background-color: #c5e1a5; /* 파스텔 연두 */
        color: white;
        font-size: 50;
        padding: 70px;
        border: none;
        border-radius: 50px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease;
        width: 300px;
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
    }
    .element-container:has(#non_alcoholic_button_span) + div button:hover {
        background-color: #aed581;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Choose Your Drink Type (1/3)</h1>
            <h2></h2>
        </div>
        """, 
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([3, 1, 3])

    with col1:
        st.markdown('<span id="alcoholic_button_span"></span>', unsafe_allow_html=True)
        if st.button(
            "Alcoholic",
            key="alcoholic_button",
            help="Select this for alcoholic drinks",
            use_container_width=True
        ):
            st.session_state.drink_type = "Alcoholic"
            next_page()

    with col3:
        st.markdown('<span id="non_alcoholic_button_span"></span>', unsafe_allow_html=True)
        if st.button(
            "Non-Alcoholic",
            key="non_alcoholic_button",
            help="Select this for non-alcoholic drinks",
            use_container_width=True
        ):
            st.session_state.drink_type = "Non_Alcoholic"
            next_page()
    
    restart_btn()


# 여러 음식 아이콘을 보여주고, feature들을 입력받는 함수입니다.
# 이때, st.session_state.drink_type이 "Alcoholic"이라면 ABV값은 슬라이드로 입력받도록 합니다.
# 각각 음식 사진에 대응하는 그림을 보여주고 해당 그림을 누르면 feature값을 조절하는 방식을 사용합니다.
def handle_input_by_images(drinktype):

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Explore your taste! (2/3)</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 기본 시작값은 50으로 설정합니다.
    default_value = 50.0
    feature_list = ["ABV", "boozy", "sweet", "sour", "bitter", "umami",
                    "salty", "astringent", "perceived_t", "spicy",
                    "herbal", "floral", "fruity", "nutty", "creamy", "smoky"]
    feature_dic = {}
    feature_to_idx = {}
    count = 0
    for feature in feature_list:
        feature_dic[feature] = default_value
        feature_to_idx[feature] = count
        count += 1

    # feature 순서 정보를 저장하는 dictionary 입니다. 이름으로 맵핑할 수 있어 공간에 직관적으로 접근할 수 있습니다.
    st.session_state.feature_to_index = feature_to_idx

    # ABV 값의 범위는 0~60으로 기본값은 30.0입니다. 그러나 Non-Alcoholic인 경우를 고려해 0으로 초기화합니다.
    feature_dic['ABV'] = 0.0

    # Alcoholic 이라면 ABV값을 입력받는 것이 필요합니다.
    if drinktype=="Alcoholic":
        feature_dic['ABV'] = st.slider("ABV", 0.0, 60.0, 30.0, step=0.1)

    # 모은 ingredient 사진들의 이름을 모은 list입니다.
    png_list = ['almond', 'apple', 'basil', 'bonfire', 'candy',
                       'champagne', 'chocolate', 'coffee_beans', 'cola',
                       'dark_chocolate', 'grapefruit', 'honey', 'ice_cream',
                       'lavender', 'lemon', 'lime', 'milk', 'mint', 'orange',
                       'pepper', 'pepper_hot', 'pistachio', 'pretzel', 'rose',
                       'salt']
    base_path = './ingredient_image/'
    img_path_list = []
    for png in png_list:
        img_path_list.append(base_path + png + '.png')

    png_to_idx = {}
    count = 0
    for ingredient in png_list:
        png_to_idx[ingredient] = count
        count += 1

    lemon_value = [5, 30, 20, 25, 10, -10, 10, 10, -5, 0, 5, 0]
    lime_value = [0, 30, 20, 25, 10, -15, 15, 15, -10, 0, 5, 0]
    grapefruit_value = [5, 20, 20, 25, 5, -10, 5, 5, -10, 0, 5, 0]
    honey_value = [25, -10, -10, -5, -5, -15, -5, -5, 0, 5, 0, 0]
    candy_value = [25, 5, -5, -15, -5, -10, -10, -10, 0, 0, 0, 0]
    bonfire_value = [0, 0, 0, -10, 0, 30, 0, 0, 5, -5, 0, 5]
    pepper_value = [0, 5, 15, 0, 10, -10, 5, 0, -10, -10, 20, 0]
    hot_pepper_value = [0, 5, 20, 0, 10, -10, 5, 0, -10, -10, 30, 0]
    milk_value = [0, 0, 0, 0, 10, -5, 0, 0, 0, 30, -10, -5]
    ice_cream_value = [25, -10, -10, -5, -10, -10, 0, 0, 0, 25, 0, 10]
    chocolate_value = [25, -5, -5, -5, -10, 0, 0, 0, 0, -10, 0, 0]
    mint_value = [0, 0, 0, 0, 0, -10, 25, 25, -10, 0, 10, 0]
    basil_value = [0, 0, 5, 0, 0, -5, 15, 15, -5, 0, 5, 0]
    coffee_beans_value = [0, 0, 10, 0, 0, 20, 10, 0, 5, 0, 0, 0]
    dark_chocolate_value = [0, 0, 20, 0, 0, 0, 5, 0, 0, 0, 0, 0]
    pretzel_value = [0, 0, 0, -5, 0, 10, -5, -5, 10, -5, 0, 15]
    salt_value = [0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 25]
    almond_value = [0, 0, 0, -10, -5, 10, -5, -5, 25, 0, 0, 0]
    pistachio_value = [0, 0, 5, 0, 0, 10, 0, 0, 15, 0, 5, 0]
    rose_value = [0, 0, 0, -5, 5, -10, 15, 20, -10, 0, 0, 0]
    lavender_value = [0, 0, 0, -5, 5, -10, 25, 15, -10, 0, 0, 0]
    cola_value = [20, 10, 5, -5, 10, -15, -10, -10, -10, 5, 15, 10]
    champagne_value = [0, 0, 0, 0, 5, -10, 0, 5, -10, -5, 0, 0]

    # img_to_idx는 사용하고자 하는 이미지 이름으로 index를 불러오며,
    # img_path_list에 저장된 image path에 접근하여 이미지를 불러올 수 있습니다.
    st.session_state.img_to_idx = png_to_idx
    st.session_state.img_path_list = img_path_list


    # create streamlit columns (5*5)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    with col1:
        st.markdown(img_to_html(img_path_list[png_to_idx['lemon']]), unsafe_allow_html=True)
        lemon = st.checkbox("lemon", key="lemon", help="add strong sour, bitter, fruity taste")
        if lemon:
            # 0 -> 1로 넘어가는 경우에는 choice_state를 업데이트 합니다.
            if st.session_state.choice['lemon'] == 0:
                st.session_state.choice_state += lemon_value
            st.session_state.choice['lemon'] = 1
        else:
            # 1 -> 0으로 넘어가는 경우에는 choice_state를 업데이트 합니다.
            if st.session_state.choice['lemon'] == 1:
                st.session_state.choice_state -= lemon_value
            st.session_state.choice['lemon'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['bonfire']]), unsafe_allow_html=True)
        bonfire = st.checkbox("bonfire", key="bonfire", help="add strong smoky taste")
        if bonfire:
            # 0 -> 1로 넘어가는 경우에는 choice_state를 업데이트 합니다.
            if st.session_state.choice['bonfire'] == 0:
                st.session_state.choice_state += bonfire_value
            st.session_state.choice['bonfire'] = 1
        else:
            # 1 -> 0으로 넘어가는 경우에는 choice_state를 업데이트 합니다.
            if st.session_state.choice['bonfire'] == 1:
                st.session_state.choice_state -= bonfire_value
            st.session_state.choice['bonfire'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['chocolate']]), unsafe_allow_html=True)
        chocolate = st.checkbox("chocolate", key="chocolate", help="add strong sweet taste")
        if chocolate:
            if st.session_state.choice['chocolate'] == 0:
                st.session_state.choice_state += chocolate_value
            st.session_state.choice['chocolate'] = 1
        else:
            if st.session_state.choice['chocolate'] == 1:
                st.session_state.choice_state -= chocolate_value
            st.session_state.choice['chocolate'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['mint']]), unsafe_allow_html=True)
        mint = st.checkbox("mint", key="mint", help="add herbal and floral taste")
        if mint:
            if st.session_state.choice['mint'] == 0:
                st.session_state.choice_state += mint_value
            st.session_state.choice['mint'] = 1
        else:
            if st.session_state.choice['mint'] == 1:
                st.session_state.choice_state -= mint_value
            st.session_state.choice['mint'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['almond']]), unsafe_allow_html=True)
        almond = st.checkbox("almond", key="almond", help="add strong nutty taste")
        if almond:
            if st.session_state.choice['almond'] == 0:
                st.session_state.choice_state += almond_value
            st.session_state.choice['almond'] = 1
        else:
            if st.session_state.choice['almond'] == 1:
                st.session_state.choice_state -= almond_value
            st.session_state.choice['almond'] = 0

    with col2:
        st.markdown(img_to_html(img_path_list[png_to_idx['lime']]), unsafe_allow_html=True)
        lime = st.checkbox("lime", key="lime", help="add strong sour, bitter, fruity taste")
        if lime:
            if st.session_state.choice['lime'] == 0:
                st.session_state.choice_state += lime_value
            st.session_state.choice['lime'] = 1
        else:
            if st.session_state.choice['lime'] == 1:
                st.session_state.choice_state -= lime_value
            st.session_state.choice['lime'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['milk']]), unsafe_allow_html=True)
        milk = st.checkbox("milk", key="milk", help="add umami, creamy taste")
        if milk:
            if st.session_state.choice['milk'] == 0:
                st.session_state.choice_state += milk_value
            st.session_state.choice['milk'] = 1
        else:
            if st.session_state.choice['milk'] == 1:
                st.session_state.choice_state -= milk_value
            st.session_state.choice['milk'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['pretzel']]), unsafe_allow_html=True)
        pretzel = st.checkbox("pretzel", key="pretzel", help="add nutty and salty taste")
        if pretzel:
            if st.session_state.choice['pretzel'] == 0:
                st.session_state.choice_state += pretzel_value
            st.session_state.choice['pretzel'] = 1
        else:
            if st.session_state.choice['pretzel'] == 1:
                st.session_state.choice_state -= pretzel_value
            st.session_state.choice['pretzel'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['dark_chocolate']]), unsafe_allow_html=True)
        dark_chocolate = st.checkbox("dark chocolate", key="dark chocolate", help="add strong bitter taste")
        if dark_chocolate:
            if st.session_state.choice['dark_chocolate'] == 0:
                st.session_state.choice_state += dark_chocolate_value
            st.session_state.choice['dark_chocolate'] = 1
        else:
            if st.session_state.choice['dark_chocolate'] == 1:
                st.session_state.choice_state -= dark_chocolate_value
            st.session_state.choice['dark_chocolate'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['lavender']]), unsafe_allow_html=True)
        lavender = st.checkbox("lavender", key="lavender", help="add strong herbal and floral taste")
        if lavender:
            if st.session_state.choice['lavender'] == 0:
                st.session_state.choice_state += lavender_value
            st.session_state.choice['lavender'] = 1
        else:
            if st.session_state.choice['lavender'] == 1:
                st.session_state.choice_state -= lavender_value
            st.session_state.choice['lavender'] = 0
    with col3:
        st.markdown(img_to_html(img_path_list[png_to_idx['grapefruit']]), unsafe_allow_html=True)
        grapefruit = st.checkbox("grapefruit", key="grapefruit", help="add strong sour, bitter, fruity taste")
        if grapefruit:
            if st.session_state.choice['grapefruit'] == 0:
                st.session_state.choice_state += grapefruit_value
            st.session_state.choice['grapefruit'] = 1
        else:
            if st.session_state.choice['grapefruit'] == 1:
                st.session_state.choice_state -= grapefruit_value
            st.session_state.choice['grapefruit'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['pepper']]), unsafe_allow_html=True)
        pepper = st.checkbox("pepper", key="pepper", help="add bitter, umami, spicy taste")
        if pepper:
            if st.session_state.choice['pepper'] == 0:
                st.session_state.choice_state += pepper_value
            st.session_state.choice['pepper'] = 1
        else:
            if st.session_state.choice['pepper'] == 1:
                st.session_state.choice_state -= pepper_value
            st.session_state.choice['pepper'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['basil']]), unsafe_allow_html=True)
        basil = st.checkbox("basil", key="basil", help="add herbal and floral taste")
        if basil:
            if st.session_state.choice['basil'] == 0:
                st.session_state.choice_state += basil_value
            st.session_state.choice['basil'] = 1
        else:
            if st.session_state.choice['basil'] == 1:
              st.session_state.choice_state -= basil_value
            st.session_state.choice['basil'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['pistachio']]), unsafe_allow_html=True)
        pistachio = st.checkbox("pistachio", key="pistachio", help="add umami and nutty taste")
        if pistachio:
            if st.session_state.choice['pistachio'] == 0:
                st.session_state.choice_state += pistachio_value
            st.session_state.choice['pistachio'] = 1
        else:
            if st.session_state.choice['pistachio'] == 1:
                st.session_state.choice_state -= pistachio_value
            st.session_state.choice['pistachio'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['cola']]), unsafe_allow_html=True)
        cola = st.checkbox("coca-cola", key="coca-cola", help="add strong sweet and spicy taste")
        if cola:
            if st.session_state.choice['cola'] == 0:
                st.session_state.choice_state += cola_value
            st.session_state.choice['cola'] = 1
        else:
            if st.session_state.choice['cola'] == 1:
                st.session_state.choice_state -= cola_value
            st.session_state.choice['cola'] = 0
    with col4:
        st.markdown(img_to_html(img_path_list[png_to_idx['honey']]), unsafe_allow_html=True)
        honey = st.checkbox('honey', key='honey', help='add strong sweet taste')
        if honey:
            if st.session_state.choice['honey'] == 0:
                st.session_state.choice_state += honey_value
            st.session_state.choice['honey'] = 1
        else:
            if st.session_state.choice['honey'] == 1:
                st.session_state.choice_state -= honey_value
            st.session_state.choice['honey'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['ice_cream']]), unsafe_allow_html=True)
        ice_cream = st.checkbox('ice cream', key='ice cream', help='add strong creamy, sweet and little salty taste')
        if ice_cream:
            if st.session_state.choice['ice_cream'] == 0:
                st.session_state.choice_state += ice_cream_value
            st.session_state.choice['ice_cream'] = 1
        else:
            if st.session_state.choice['ice_cream'] == 1:
                st.session_state.choice_state -= ice_cream_value
            st.session_state.choice['ice_cream'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['salt']]), unsafe_allow_html=True)
        salt = st.checkbox('salt', key='salt', help='add strong salty taste')
        if salt:
            if st.session_state.choice['salt'] == 0:
                st.session_state.choice_state += salt_value
            st.session_state.choice['salt'] = 1
        else:
            if st.session_state.choice['salt'] == 1:
                st.session_state.choice_state -= salt_value
            st.session_state.choice['salt'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['champagne']]), unsafe_allow_html=True)
        champagne = st.checkbox('champagne', key='champagne', help='add weak umami, floral taste')
        if champagne:
            if st.session_state.choice['champagne'] == 0:
                st.session_state.choice_state += champagne_value
            st.session_state.choice['champagne'] = 1
        else:
            if st.session_state.choice['champagne'] == 1:
                st.session_state.choice_state -= champagne_value
            st.session_state.choice['champagne'] = 0
    with col5:
        st.markdown(img_to_html(img_path_list[png_to_idx['candy']]), unsafe_allow_html=True)
        candy = st.checkbox('candy', key='candy', help='add strong sweet taste')
        if candy:
            if st.session_state.choice['candy'] == 0:
                st.session_state.choice_state += candy_value
            st.session_state.choice['candy'] = 1
        else:
            if st.session_state.choice['candy'] == 1:
                st.session_state.choice_state -= candy_value
            st.session_state.choice['candy'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['pepper_hot']]), unsafe_allow_html=True)
        hot_pepper = st.checkbox('hot pepper', key='hot pepper', help='add strong bitter, umami, spicy taste')
        if hot_pepper:
            if st.session_state.choice['hot_pepper'] == 0:
                st.session_state.choice_state += hot_pepper_value
            st.session_state.choice['hot_pepper'] = 1
        else:
            if st.session_state.choice['hot_pepper'] == 1:
                st.session_state.choice_state -= hot_pepper_value
            st.session_state.choice['hot_pepper'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['coffee_beans']]), unsafe_allow_html=True)
        coffee_beans = st.checkbox('coffee beans', key='coffee beans', help='add smoky taste')
        if coffee_beans:
            if st.session_state.choice['coffee_beans'] == 0:
                st.session_state.choice_state += coffee_beans_value
            st.session_state.choice['coffee_beans'] = 1
        else:
            if st.session_state.choice['coffee_beans'] == 1:
                st.session_state.choice_state -= coffee_beans_value
            st.session_state.choice['coffee_beans'] = 0

        st.markdown(img_to_html(img_path_list[png_to_idx['rose']]), unsafe_allow_html=True)
        rose = st.checkbox('rose', key='rose', help='add strong floral taste')
        if rose:
            if st.session_state.choice['rose'] == 0:
                st.session_state.choice_state += rose_value
            st.session_state.choice['rose'] = 1
        else:
            if st.session_state.choice['rose'] == 1:
                st.session_state.choice_state -= rose_value
            st.session_state.choice['rose'] = 0

    print("choice_state: ", st.session_state.choice_state)

    st.write('Your Profile!')
    fig1, ax1 = plt.subplots(subplot_kw={'projection': 'polar'})

    labels = ['sweet', 'sour', 'bitter', 'fruity', 'umami', 'smoky',
            'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty']
    values = list(st.session_state.choice_state)
    values += values[:1]
    theta = np.linspace(0.0, 2 * np.pi, len(labels), endpoint=False)
    theta = np.append(theta, theta[0])
    ax1.fill(theta, values, 'b', alpha=0.1)
    ax1.plot(theta, values, 'b', marker='o')
    ax1.set_xticks(theta[:-1])
    ax1.set_xticklabels(labels)
    st.pyplot(fig1)


    # Set My Taste 버튼을 누르면 다음 페이지로 넘어가며, update된 feature dictionary를 업데이트 합니다.
    if st.button("Set My Taste", type='primary', use_container_width=True):
        selection_list = st.session_state.choice
        print("Choice: ", selection_list)
        # Perceived_temperature, boozy, astringent는 제외하였습니다. 해당 feature들은 랜덤하거나, ABV, bitter 값에 따라 조절됩니다.
        feature_selection = ['sweet', 'sour', 'bitter', 'fruity', 'umami', 'smoky',
                             'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty']
        value_selection = np.zeros(len(feature_selection))

        for choice, value in selection_list.items():
            if value==1: # 선택된 재료에 대해서만 feature값을 업데이트 합니다.
                if choice == "lemon":
                    value_selection += lemon_value
                elif choice == "lime":
                    value_selection += lime_value
                elif choice == "grapefruit":
                    value_selection += grapefruit_value
                elif choice == "honey":
                    value_selection += honey_value
                elif choice == "candy":
                    value_selection += candy_value
                elif choice == "bonfire":
                    value_selection += bonfire_value
                elif choice == "pepper":
                    value_selection += pepper_value
                elif choice == "hot_pepper":
                    value_selection += hot_pepper_value
                elif choice == "milk":
                    value_selection += milk_value
                elif choice == "ice_cream":
                    value_selection += ice_cream_value
                elif choice == "chocolate":
                    value_selection += chocolate_value
                elif choice == "mint":
                    value_selection += mint_value
                elif choice == "basil":
                    value_selection += basil_value
                elif choice == "coffee_beans":
                    value_selection += coffee_beans_value
                elif choice == "dark_chocolate":
                    value_selection += dark_chocolate_value
                elif choice == "pretzel":
                    value_selection += pretzel_value
                elif choice == "salt":
                    value_selection += salt_value
                elif choice == "almond":
                    value_selection += almond_value
                elif choice == "pistachio":
                    value_selection += pistachio_value
                elif choice == "rose":
                    value_selection += rose_value
                elif choice == "lavender":
                    value_selection += lavender_value
                elif choice == "cola":
                    value_selection += cola_value
                elif choice == "champagne":
                    value_selection += champagne_value
                else:
                    print("----!Invalid Choice!----")

        feature_dic = update_feature(feature_dic, feature_selection, value_selection)
        st.session_state.main_feature_values = feature_dic
        print(feature_dic)
        next_page()

    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart"):
            initialize_state()
            st.rerun()


def handle_input_seed_ingredient(loading_animations):
    st.markdown(
        """
        <style>
        .element-container:has(#select_button_span) + div button {
            background-color: #d3d3d3; /* 그레이 */
            color: black;
            font-size: 24px;
            border: none;
            border-radius: 50px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
            width: 220px;
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            word-break: keep-all; 
            white-space: pre;
        }
        .element-container:has(#select_button_span) + div button:hover {
            background-color: #c0c0c0;
        }
        .element-container:has(#selected_button_span) + div button {
            background-color: #ffe4b5; /* 노란색 */
            color: black;
            font-size: 24px;
            border: none;
            border-radius: 10px;W
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease;
            width: 220px;
            height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            word-break: break-word;
            white-space: pre;
        }
        .element-container:has(#selected_button_span) + div button:hover {
            background-color: #ffd700;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Input seed ingredient! (3/3)</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    # initialize seed ingredient (should be in string value)
    if "selected_ingredient" not in st.session_state:
        st.session_state.selected_ingredient = ""
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = -1

    main_features = st.session_state.main_feature_values
    main_features['astringent'] = main_features['bitter'] * 0.9
    main_features['boozy'] = main_features['ABV'] * 0.9
    main_features['perceived_t'] = random.uniform(0.3, 0.5)*100
    main_features['seed'] = st.session_state.selected_ingredient # None value for initial seed ingredient

    # feature value should be no bigger than 100 and no less tham 0
    st.session_state.main_feature_values = filter_feature(main_features)

    # filter로 요청하면, profile의 feature값과 차이가 적은 재료 top 10개를 불러와서 선택하도록 합니다.
    # 이때, 각 재료의 특성 값이 그래프로 나타나도록 합니다.
    response = requests.post(
        'http://localhost:8000/filter',
        json={
            "features": st.session_state.main_feature_values,
            "selected_ingredient": st.session_state.selected_ingredient,
            "selected_index": st.session_state.selected_index
        }
    )

    if response.status_code == 200:
        seed_ingredient_list = response.json()
    else:
        st.write("Failed to get a filtered ingredient list. Please try again later.")
        
    # Button 형태로 변환 3x3
    st.markdown("Choose your seed ingredients:")
    for i in range(0, len(seed_ingredient_list['ingredients'])//3 * 3, 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(seed_ingredient_list['ingredients']):
                ingredient = seed_ingredient_list['ingredients'][i + j]
                if st.session_state.selected_ingredient == ingredient:
                    button_style = "selected_button_span"
                else:
                    button_style = "select_button_span"
                with cols[j]:
                    st.markdown(f'<span id={button_style}></span>', unsafe_allow_html=True)
                    if st.button(
                        ingredient,
                        key=f"ingredient_button_{i + j}",
                        help=f"{seed_ingredient_list['description'][ingredient]['description']}",  # 재료에 대한 설명
                        use_container_width=True,
                        on_click=lambda ingredient=ingredient, index=i+j: st.session_state.update(selected_ingredient=ingredient, selected_index=index)
                    ):
                        pass

    selected_flavor = seed_ingredient_list['flavor'].get(st.session_state.selected_ingredient, {})
    # 맛 그래프 표시
    if selected_flavor:
        col1, col2, col3 = st.columns([1, 30, 1])
        # 맛 그래프 표시
        with col2:
            st.markdown("### Flavor Profile")
            labels = list(selected_flavor.keys())
            labels = labels[-4:] + labels[:-4]
            values = list(selected_flavor.values())
            values = values[-4:] + values[:-4]
            values += values[:1]  # close the circle
            theta = np.linspace(0.0, 2 * np.pi, len(labels), endpoint=False)
            theta = np.append(theta, theta[0])

            fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

            # Draw the polygon representing the data
            ax.fill(theta, values, color='b', alpha=0.1)
            ax.plot(theta, values, color='b', marker='o', linestyle='-', linewidth=2, alpha=0.3)

            # Add labels to each axis
            ax.set_xticks(theta[:-1])
            ax.set_xticklabels(labels, fontsize=7, fontweight='bold')

            # Add grid lines
            ax.yaxis.grid(True, color='gray', linestyle='--', linewidth=0.5)
            ax.xaxis.grid(True, color='gray', linestyle='--', linewidth=0.5)

            # Set the range for the radial axes # REMOVE
            ax.set_ylim(0, 100)
            ax.set_yticklabels([])

            # Add a title
            st.pyplot(fig)
    
    if st.button(
        "Determine",
        key="determine_choice",
        help="Determine the seed ingredient",
        use_container_width=True,
        type='primary'
    ):
        print("main_feature_values: ", st.session_state.main_feature_values)
        main_features = st.session_state.main_feature_values
        if st.session_state.selected_ingredient == "":
            main_features['seed'] = random.choice(seed_ingredient_list['ingredients'])
        # main_features['seed'] = st.session_state.selected_ingredient
        st.session_state.loading_animation = random.choice(loading_animations)
        st.session_state.main_feature_values = main_features
        next_page()

    col1, col2, col3 = st.columns([3, 1, 3])

    with col2:
        if st.button("Restart", key="restart"):
            initialize_state()
            st.rerun()


def show_loading_page():
    # Scroll to the top of the page
    st.markdown("""
        <style>
        /* Hide scrollbar */
        ::-webkit-scrollbar {
            display: none;
        }
        </style>
        <script>
        window.scrollTo(0, 0);
        </script>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Loading Your Recommendation...</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st_lottie(st.session_state.loading_animation, height=500, key=f"loading_animation_{random.randint(0, 1000)}")
    # Simulate random latency between 0.5 and 2 seconds
    time.sleep(random.uniform(0.5, 2))

    main_features = st.session_state.main_feature_values
    print("!!!![st.session_state.main_feature_values]!!!!!!", main_features)

    # response -> (recipe: result_recipe, profile: user_recipe_profile)인 딕셔너리임
    response = requests.post('http://localhost:8000/predict', json=main_features)

    if response.status_code == 200:
        predict = response.json()
        st.session_state.prediction_result = predict
        next_page()
    else:
        st.write("Failed to get a cocktail recommendation. Please try again later.")

    restart_btn()



def show_recommendation(prediction, cocktail_animations):
    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Your Cocktail Recommendation</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
        <style>
        .centered-title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Calculate the height for the animation
    num_ingredients = len(prediction['recipe'])
    base_height = 250
    additional_height_per_ingredient = 25
    animation_height = base_height + (num_ingredients * additional_height_per_ingredient)

    if "cocktail_animation" not in st.session_state:
        st.session_state.cocktail_animation = random.choice(cocktail_animations)

    # Create tabs
    tab1, tab2 , tab3 = st.tabs(["Details", "Graphs","Live Bar"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st_lottie(st.session_state.cocktail_animation, height=animation_height, key="cocktail_animation")
            # # Display image
            # st.image(cocktail['image_path'], width=300)

        with col2:
            st.markdown("<div class='centered-title'>Recommend Recipe:</div>", unsafe_allow_html=True)
            for ingredient, amount in prediction['recipe'].items():
                st.write(f"- {ingredient}: {round(amount, 2)}ml")
            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st_lottie(st.session_state.cocktail_animation, height=animation_height, key="cocktail_animation_2")
            # # Display image
            # st.image(cocktail['image_path'], width=300)

        with col2:
            st.markdown("<div class='centered-title'>Recommend Recipe:</div>", unsafe_allow_html=True)
            print(prediction.keys())
            for ingredient, amount in prediction['live_recipe'].items():
                st.write(f"- {ingredient}: {round(amount, 2)}ml")
            st.markdown("</div>", unsafe_allow_html=True)
    with tab2:
        col3, col4 = st.columns(2)

        with col3:
            # Plot Recipe as a Pie Chart
            fig1, ax1 = plt.subplots()
            ax1.pie(prediction['recipe'].values(), labels=prediction['recipe'].keys(), autopct='%1.1f%%', startangle=90)
            ax1.axis('equal')
            st.pyplot(fig1)

        with col4:
            # Plot Combined Flavors as a Radar Chart
            fig2, ax2 = plt.subplots(subplot_kw={'projection': 'polar'})

            recipe_profile = prediction['profile']
            labels = list(recipe_profile.keys())
            values = list(recipe_profile.values())
            values += values[:1]
            theta = np.linspace(0.0, 2 * np.pi, len(labels), endpoint=False)
            theta = np.append(theta, theta[0])
            ax2.fill(theta, values, 'b', alpha=0.1)
            ax2.plot(theta, values, 'b', marker='o')
            ax2.set_xticks(theta[:-1])
            ax2.set_xticklabels(labels)
            st.pyplot(fig2)

    # create feedback slider for 1-5 feedback rating input
    # 한번 submit하면 여러번 submit이 되도록 하면 안됩니다.
    if not st.session_state.is_submit:
        # using streamlit default slider
        # st.session_state.feedback_ratings = st.slider('How do you like this recommendation?', 1, 5)
        # using start rating component
        st.session_state.feedback_ratings = st_star_rating("How do you like this recommendation?", maxValue=5, defaultValue=3, key="StarRating", dark_theme=True)
        if st.button("Submit Feedback"):

            with open('./feedback/feedback.json', 'r') as f:
                feedback = json.load(f)

            ingredient_list = []
            amount_list = []
            for ing, amount in st.session_state.prediction_result['recipe'].items():
                ingredient_list.append(ing)
                amount_list.append(amount)

            feedback['feedback_info'].append({"input_features": st.session_state.main_feature_values,
                                            "output_ingredients": ingredient_list,
                                            "output_amounts" : amount_list,
                                            "feedback_rating": st.session_state.feedback_ratings})

            with open('./feedback/feedback.json', 'w') as fw:
                json.dump(feedback, fw)

            st.write("Thanks!")
            st.session_state.is_submit = True

    restart_btn()


# def handle_feedback_page():
#     st.title('How do you like this recommendation?')

#     feedback = st.slider('How do you like this recommendation?', 0, 5)

#     restart_btn()
