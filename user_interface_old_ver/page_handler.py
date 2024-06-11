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
    st.session_state.choice = None
    st.session_state.choice2 = None
    st.session_state.loading_animation = None
    st.session_state.feedback_ratings = 0
    st.session_state.is_submit = False

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
    col1, col2, col3 = st.columns([3, 2, 3])
    with col2:
        if st.button("Start Your Journey"):
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
        padding: 70px; /* 위아래로 길게 */
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
        padding: 70px; /* 위아래로 길게 */
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
            <h1>Choose Your Drink Type</h1>
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

    for i in range(10):
      col1, col2, col3 = st.columns([3, 1, 3])
    
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()


# 여러 음식 아이콘을 보여주고, feature들을 입력받는 함수입니다.
# 이때, st.session_state.drink_type이 "Alcoholic"이라면 ABV값은 슬라이드로 입력받도록 합니다.
# 각각 음식 사진에 대응하는 그림을 보여주고 해당 그림을 누르면 feature값을 조절하는 방식을 사용합니다.
def handle_input_by_images_1(drinktype):

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Explore your taste!</h1>
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
        
    # img_to_idx는 사용하고자 하는 이미지 이름으로 index를 불러오며,
    # img_path_list에 저장된 image path에 접근하여 이미지를 불러올 수 있습니다.
    st.session_state.img_to_idx = png_to_idx
    st.session_state.img_path_list = img_path_list

    
    # streamlit의 image()는 image 자체를 버튼으로 사용할 수 없습니다. 따라서 html기반의 markdown을 사용하도록 합니다.
    # lemon, lime, grapefruit, honey, candy 이미지를 보여주고, sweet, sour, fruity를 조절합니다.
    # 3칸으로 나눠지는 경우 320x418(height x width)으로 이미지를 resize 했으며
    # 2칸으로 나눠지는 경우 520x520(height x width)으로 이미지를 resize 했습니다.


    col1, col2, col3  = st.columns([1, 1, 1])
    with col1:
        st.markdown(img_to_html(img_path_list[png_to_idx['lemon']]), unsafe_allow_html=True)
    with col2:
        st.markdown(img_to_html(img_path_list[png_to_idx['lime']]), unsafe_allow_html=True)
    with col3:
        st.markdown(img_to_html(img_path_list[png_to_idx['grapefruit']]), unsafe_allow_html=True)

    col4, col5 = st.columns([1, 1])
    with col4:
        st.markdown(img_to_html(img_path_list[png_to_idx['honey']]), unsafe_allow_html=True)
    with col5:
        st.markdown(img_to_html(img_path_list[png_to_idx['candy']]), unsafe_allow_html=True)

    # selectbox를 이용하여 flavor를 선택합니다.
    st.session_state.choice = st.selectbox("Choose Your Flavor!", ["lemon", "lime", "grapefruit", "honey", "candy", "None"],
                                           key = 'select flavor')

    # Get Recipe 버튼을 누르면 다음 페이지로 넘어가며, update된 feature dictionary를 업데이트 합니다.
    if st.button("Get Recipe"):
        choice = st.session_state.choice
        print("Choice: ", choice)
        # Perceived_temperature, boozy, astringent는 제외하였습니다. 해당 feature들은 랜덤하거나, ABV, bitter 값에 따라 조절됩니다.
        feature_selection = ['sweet', 'sour', 'bitter', 'fruity', 'umami', 'smoky',
                             'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty']
        value_selection = np.zeros(len(feature_selection))

        if choice == "lemon":
            value_selection = [5, 30, 20, 25, 10, -10, 10, 10, -5, 0, 5, 0]
        elif choice == "lime":
            value_selection = [0, 30, 20, 25, 10, -15, 15, 15, -10, 0, 5, 0]
        elif choice == "grapefruit":
            value_selection = [5, 20, 20, 25, 5, -10, 5, 5, -10, 0, 5, 0]
        elif choice == "honey":
            value_selection = [25, -10, -10, -5, -5, -15, -5, -5, 0, 5, 0, 0]
        elif choice == "candy":
            value_selection = [25, 5, -5, -15, -5, -10, -10, -10, 0, 0, 0, 0]
        elif choice == "None":
            pass
        else:
            print("----!Invalid Choice!----")

        feature_dic = update_feature(feature_dic, feature_selection, value_selection)
        st.session_state.main_feature_values = feature_dic
        print(feature_dic)
        next_page()


    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()


def handle_input_by_images_2():

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Explore your taste!</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("Choose one flavor from each row!")

    feature_dic = st.session_state.main_feature_values
    img_path_list = st.session_state.img_path_list
    png_to_idx = st.session_state.img_to_idx

    # 모닥불, 그일린 나무, 고추, 할라피뇨 이미지를 보여주고, spicy, smoky를 조절합니다.
    # 3칸으로 나눠지는 경우 320x418(height x width)으로 이미지를 resize 했으며
    # 2칸으로 나눠지는 경우 520x520(height x width)으로 이미지를 resize 했습니다.

    col1, col2, col3  = st.columns([1, 1, 1])
    with col1:
        st.markdown(img_to_html(img_path_list[png_to_idx['bonfire']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['milk']]), unsafe_allow_html=True)

    with col2:
        st.markdown(img_to_html(img_path_list[png_to_idx['pepper']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['ice_cream']]), unsafe_allow_html=True)

    with col3:
        st.markdown(img_to_html(img_path_list[png_to_idx['pepper_hot']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['chocolate']]), unsafe_allow_html=True)

    st.session_state.choice = st.selectbox("Choose Your Flavor 1", ['bonfire', 'pepper', 'hot pepper', 'None'], key='select flavor 1')
    st.session_state.choice2 = st.selectbox("Choose Your Flavor 2", ['milk', 'ice cream', 'chocolate', 'None'], key='select flavor 2')

    # Get Recipe 버튼을 누르면 다음 페이지로 넘어가며, update된 feature dictionary를 업데이트 합니다.
    if st.button("Get Recipe"):
        choice = st.session_state.choice
        choice2 = st.session_state.choice2
        print("Choice: ", choice)
        print("Choice2: ", choice2)

        feature_selection = ['sweet', 'sour', 'bitter', 'fruity', 'umami', 'smoky',
                             'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty']
        value_selection = np.zeros(len(feature_selection))
        value_selection2 = np.zeros(len(feature_selection))

        if choice == "bonfire":
            value_selection = [0, 0, 0, -10, 0, 30, 0, 0, 5, -5, 0, 5]
        elif choice == "pepper":
            value_selection = [0, 5, 15, 0, 10, -10, 5, 0, -10, -10, 20, 0]
        elif choice == "hot pepper":
            value_selection = [0, 5, 20, 0, 10, -10, 5, 0, -10, -10, 30, 0]
        elif choice == "None":
            pass
        else:
            print("----!Invalid Choice 1!----")

        if choice2 == "milk":
            value_selection2 = [0, 0, 0, 0, 10, -5, 0, 0, 0, 30, -10, -5]
        elif choice2 == "ice cream":
            value_selection2 = [25, -10, -10, -5, -10, -10, 0, 0, 0, 25, 0, 10]
        elif choice2 == "chocolate":
            value_selection2 = [25, -5, -5, -5, -10, 0, 0, 0, 0, -10, 0, 0]
        elif choice == "None":
            pass
        else:
            print("----!Invalid Choice 2!----")

        feature_dic = update_feature(feature_dic, feature_selection, value_selection)
        feature_dic = update_feature(feature_dic, feature_selection, value_selection2)
        st.session_state.main_feature_values = feature_dic
        print(feature_dic)
        next_page()


    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()


def handle_input_by_images_3():

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Explore your taste!</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("Choose one ingredient from each row!")

    feature_dic = st.session_state.main_feature_values
    img_path_list = st.session_state.img_path_list
    png_to_idx = st.session_state.img_to_idx

    # 민트, 바질, 커피콩, 다크초콜릿, 프레첼, 소금, 아몬드, 피스타치오를 보여주고 herbal, bitter, salty, nutty등을 입력받습니다.
    # 3칸으로 나눠지는 경우 320x418(height x width)으로 이미지를 resize 했으며
    # 2칸으로 나눠지는 경우 520x520(height x width)으로 이미지를 resize 했습니다.

    col1, col2, col3, col4  = st.columns([1, 1, 1, 1])
    with col1:
        st.markdown(img_to_html(img_path_list[png_to_idx['mint']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['pretzel']]), unsafe_allow_html=True)

    with col2:
        st.markdown(img_to_html(img_path_list[png_to_idx['basil']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['salt']]), unsafe_allow_html=True)

    with col3:
        st.markdown(img_to_html(img_path_list[png_to_idx['coffee_beans']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['almond']]), unsafe_allow_html=True)
    
    with col4:
        st.markdown(img_to_html(img_path_list[png_to_idx['dark_chocolate']]), unsafe_allow_html=True)
        st.markdown(img_to_html(img_path_list[png_to_idx['pistachio']]), unsafe_allow_html=True)

    
    st.session_state.choice = st.selectbox("Choose Your Flavor 1", ['mint', 'basil', 'coffee beans', 'dark chocolate', 'None'], key='select flavor 1')
    st.session_state.choice2 = st.selectbox("Choose Your Flavor 2", ['pretzel', 'salt', 'almond', 'pistachio', 'None'], key='select flavor 2')
    

    # Get Recipe 버튼을 누르면 다음 페이지로 넘어가며, update된 feature dictionary를 업데이트 합니다.
    if st.button("Get Recipe"):
        choice = st.session_state.choice
        choice2 = st.session_state.choice2
        print("Choice: ", choice)
        print("Choice2: ", choice2)

        feature_selection = ['sweet', 'sour', 'bitter', 'fruity', 'umami', 'smoky',
                             'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty']
        value_selection = np.zeros(len(feature_selection))
        value_selection2 = np.zeros(len(feature_selection))

        if choice == "mint":
            value_selection = [0, 0, 0, 0, 0, -10, 25, 25, -10, 0, 10, 0]
        elif choice == "basil":
            value_selection = [0, 0, 5, 0, 0, -5, 15, 15, -5, 0, 5, 0]
        elif choice == "coffee beans":
            value_selection = [0, 0, 10, 0, 0, 20, 10, 0, 5, 0, 0, 0]
        elif choice == "dark chocolate":
            value_selection = [0, 0, 20, 0, 0, 0, 5, 0, 0, 0, 0, 0]
        elif choice == "None":
            pass
        else:
            print("----!Invalid Choice 1!----")

        if choice2 == "pretzel":
            value_selection2 = [0, 0, 0, -5, 0, 10, -5, -5, 10, -5, 0, 15]
        elif choice2 == "salt":
            value_selection2 = [0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 5, 25]
        elif choice2 == "almond":
            value_selection2 = [0, 0, 0, -10, -5, 10, -5, -5, 25, 0, 0, 0]
        elif choice2 == "pistachio":
            value_selection2 = [0, 0, 5, 0, 0, 10, 0, 0, 15, 0, 5, 0]
        elif choice2 == "None":
            pass
        else:
            print("----!Invalid Choice 2!----")

        feature_dic = update_feature(feature_dic, feature_selection, value_selection)
        feature_dic = update_feature(feature_dic, feature_selection, value_selection2)
        st.session_state.main_feature_values = feature_dic
        print(feature_dic)
        next_page()


    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()


def handle_input_by_images_4():

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Explore your taste!</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    feature_dic = st.session_state.main_feature_values
    img_path_list = st.session_state.img_path_list
    png_to_idx = st.session_state.img_to_idx

    # 장미, 라벤더, 탄산음료, 샴페인 등을 입력받으며, floral, creamy, sweet 값을 조절합니다.
    # 3칸으로 나눠지는 경우 320x418(height x width)으로 이미지를 resize 했으며
    # 2칸으로 나눠지는 경우 520x520(height x width)으로 이미지를 resize 했습니다.

    col1, col2, col3, col4  = st.columns([1, 1, 1, 1])
    with col1:
        st.markdown(img_to_html(img_path_list[png_to_idx['rose']]), unsafe_allow_html=True)
    with col2:
        st.markdown(img_to_html(img_path_list[png_to_idx['lavender']]), unsafe_allow_html=True)
    with col3:
        st.markdown(img_to_html(img_path_list[png_to_idx['cola']]), unsafe_allow_html=True)
    with col4:
        st.markdown(img_to_html(img_path_list[png_to_idx['champagne']]), unsafe_allow_html=True)

    st.session_state.choice = st.selectbox("Choose Your Flavor!", ['rose', 'lavender', 'coca-cola', 'champagne', 'None'], key='select flavor')

    # Get Recipe 버튼을 누르면 다음 페이지로 넘어가며, update된 feature dictionary를 업데이트 합니다.
    if st.button("Get Recipe"):
        choice = st.session_state.choice
        print("Choice: ", choice)

        feature_selection = ['sweet', 'sour', 'bitter', 'fruity', 'umami', 'smoky',
                             'herbal', 'floral', 'nutty', 'creamy', 'spicy', 'salty']
        value_selection = np.zeros(len(feature_selection))

        if choice == "rose":
            value_selection = [0, 0, 0, -5, 5, -10, 15, 20, -10, 0, 0, 0]
        elif choice == "lavender":
            value_selection = [0, 0, 0, -5, 5, -10, 25, 15, -10, 0, 0, 0]
        elif choice == "coca-cola":
            value_selection = [20, 10, 5, -5, 10, -15, -10, -10, -10, 5, 15, 10]
        elif choice == "champagne":
            value_selection = [0, 0, 0, 0, 5, -10, 0, 5, -10, -5, 0, 0]
        elif choice == "None":
            pass
        else:
            print("----!Invalid Choice!----")

        feature_dic = update_feature(feature_dic, feature_selection, value_selection)
        st.session_state.main_feature_values = feature_dic
        print(feature_dic)
        next_page()

    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()



def handle_input_seed_ingredient(loading_animations):

    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Input seed ingredient!</h1>
            <h2></h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    # initialize seed ingredient (should be in string value)
    seed_ingredient = ""

    main_features = st.session_state.main_feature_values
    main_features['astringent'] = main_features['bitter'] * 0.9
    main_features['boozy'] = main_features['ABV'] * 0.9
    main_features['perceived_t'] = random.uniform(0.3, 0.5)*100
    main_features['seed'] = seed_ingredient # None value for initial seed ingredient

    # feature value should be no bigger than 100 and no less tham 0
    st.session_state.main_feature_values = filter_feature(main_features)

    # filter로 요청하면, profile의 feature값과 차이가 적은 재료 top 10개를 불러와서 선택하도록 합니다.
    # 이때, 각 재료의 특성 값이 그래프로 나타나도록 합니다.
    response = requests.post('http://localhost:8000/filter', json=st.session_state.main_feature_values)

    if response.status_code == 200:
        seed_ingredient_list = response.json()
    else:
        st.write("Failed to get a filtered ingredient list. Please try again later.")

    seed_ingredient = st.selectbox("Choose your seed ingredients", seed_ingredient_list['ingredients'], key="select_seed_ingredient_from_list")
    selected_flavor = seed_ingredient_list['flavor'][seed_ingredient]

    # 맛 그래프 표시
    st.markdown("### Flavor Profile")
    fig1, ax1 = plt.subplots(subplot_kw={'projection': 'polar'})

    labels = list(selected_flavor.keys())
    values = list(selected_flavor.values())
    values += values[:1]
    theta = np.linspace(0.0, 2 * np.pi, len(labels), endpoint=False)
    theta = np.append(theta, theta[0])
    ax1.fill(theta, values, 'b', alpha=0.1)
    ax1.plot(theta, values, 'b', marker='o')
    ax1.set_xticks(theta[:-1])
    ax1.set_xticklabels(labels)
    st.pyplot(fig1)

    if st.button(
        "Determine",
        key="determine_choice",
        help="Determine the seed ingredient",
        use_container_width=True
    ):
        print("main_feature_values: ", st.session_state.main_feature_values)
        main_features = st.session_state.main_feature_values
        main_features['seed'] = seed_ingredient
        st.session_state.loading_animation = random.choice(loading_animations)
        st.session_state.main_feature_values = main_features
        next_page()

    for i in range(3):
      col1, col2, col3 = st.columns([3, 1, 3])

    with col2:
        if st.button("Restart", key="restart", type='primary'):
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
    print("!!!!!!!!!!", main_features)

    # response -> (recipe: result_recipe, profile: user_recipe_profile)인 딕셔너리임
    response = requests.post('http://localhost:8000/predict', json=main_features)

    if response.status_code == 200:
        predict = response.json()
        st.session_state.prediction_result = predict
        next_page()
    else:
        st.write("Failed to get a cocktail recommendation. Please try again later.")

    for i in range(3):
      col1, col2, col3 = st.columns([3, 1, 3])
      
    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()



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

    # Calculate the height for the animation
    num_ingredients = len(prediction['recipe'])
    base_height = 250
    additional_height_per_ingredient = 50
    animation_height = base_height + (num_ingredients * additional_height_per_ingredient)

    # Create tabs
    tab1, tab2 = st.tabs(["Details", "Graphs"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            cocktail_animation = random.choice(cocktail_animations)
            st_lottie(cocktail_animation, height=animation_height, key="cocktail_animation")
            # # Display image
            # st.image(cocktail['image_path'], width=300)

        with col2:
            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.write("**Recommend Recipe:**")
            for ingredient, amount in prediction['recipe'].items():
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


    col1, col2, col3 = st.columns([3, 1, 3])
    with col2:
        if st.button("Restart", key="restart", type='primary'):
            initialize_state()
            st.rerun()


# def handle_feedback_page():
#     st.title('How do you like this recommendation?')

#     feedback = st.slider('How do you like this recommendation?', 0, 5)

#     col1, col2, col3 = st.columns([3, 1, 3])
#     with col2:
#         if st.button("Restart", key="restart", type='primary'):
#             st.session_state.page = 0
#             st.rerun()
