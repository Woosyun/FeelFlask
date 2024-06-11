from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import tensorflow as tf
import json
from CocktailEmbeddingMaker import Eval
from typing import List, Dict


app = FastAPI()

# Load your trained LSTM model
model = tf.keras.models.load_model('testmodel.h5')

with open('./train_data.json', 'r') as f:
    json_data = json.load(f)

with open('./flavor.json', 'r') as f:
    flavor_data = json.load(f)
    
with open('./category.json', 'r') as f:
    category_data = json.load(f)


class Features(BaseModel):
    ABV: float
    sweet: float
    sour: float
    bitter: float
    spicy: float
    herbal: float
    floral: float
    fruity: float
    nutty: float
    boozy: float
    astringent: float
    umami: float
    salty: float
    perceived_t: float
    creamy: float
    smoky: float
    seed: str

class Recipe(BaseModel):
    recipe: Dict[str, float]
    profile: Dict[str, float]

class FilteredIngredients(BaseModel):
    ingredients: List[str]
    flavor: Dict[str, Dict[str, float]]

class Ratings(BaseModel):
    rates: int

@app.post('/db')
async def db(rates: Ratings):
    pass

# 사용자의 profile을 입력으로, 가장 값이 높은 feature 3개를 뽑습니다.
# 해당 feature들과 가장 유사한 값을 가지는 ingredient를 여러개 뽑아 list로 반환합니다.
@app.post("/filter", response_model=FilteredIngredients)
async def filter(features: Features):
    try:
        # 각 ingredient name과 이름을 제외한 ingredient flavor 정보가 맵핑되도록 합니다.
        flavor_dic = {}
        for flavor in flavor_data:
            element = {}
            for feature, value in flavor.items():
                if feature != "name" and feature != "ID":
                    element[feature] = value
            flavor_dic[flavor['name']] = element

        user_profile = {'ABV': features.ABV,
                          'sweet' : features.sweet,
                          'sour' : features.sour,
                          'bitter' : features.bitter,
                          'spicy' : features.spicy,
                          'herbal' : features.herbal,
                          'floral' : features.floral,
                          'fruity' : features.fruity,
                          'nutty' : features.nutty,
                          'boozy' : features.boozy,
                          'astringent' : features.astringent,
                          'umami' : features.umami,
                          'salty' : features.salty,
                          'Perceived_temperature' : features.perceived_t,
                          'creamy' : features.creamy,
                          'smoky' : features.smoky,
                          }

        sorted_values = []
        for item in user_profile.items():
            # 알콜이 없는 음료를 요구한 경우에, ABV 정보는 제외하도록 합니다.
            if (user_profile['ABV'] == 0 and item[0] == 'ABV'):
                continue
            sorted_values.append(item)

        sorted_values = sorted(sorted_values, key=lambda x: x[1], reverse=True)

        # 가장 특징적인 5개의 feature값을 가지는 feature들을 추출해 냅니다.
        top_5_features = sorted_values[:5]

        # 알콜이 포함되는 경우에는 ABV값도 score 계산에 포함시킵니다.
        if user_profile['ABV'] != 0: # ABV가 0이 아닌 경우에는 ABV값도 포함합니다.
            if ('ABV', user_profile['ABV']) not in top_5_features:
                top_5_features.append(('ABV', user_profile['ABV']))

        # lower is better
        filter_score = {}
        for ing_name, feature_list in flavor_dic.items():
            filter_score[ing_name] = 0
            for feature, value in top_5_features:
                filter_score[ing_name] += abs(feature_list[feature] - value)

        sorted_ingredient = []
        for item in filter_score.items():
            sorted_ingredient.append(item)
        sorted_ingredient = sorted(sorted_ingredient, key=lambda x: x[1])
        top_10_ingredient = []

        # ABV가 0, 즉 알콜이 들어가지 않는 경우에는 재료에서 알콜이 포함되어 있는 재료를
        # 선정해서는 안됩니다. 위에 top 5 feature에서 ABV값이 0이기 때문에 선택될 일이 없음으로
        # top 10 재료 선정에서만 주의하면 됩니다.
        if user_profile['ABV'] == 0:
            count = 0
            for ing_name, score in sorted_ingredient:
                # Mixer 카테고리에 속하고, ABV가 0인 경우에 추가합니다.
                if (flavor_dic[ing_name]['ABV'] == 0) and ('Mixer' in category_data[ing_name]):
                    top_10_ingredient.append(ing_name)
                    count += 1
                if count == 10: # 재료가 10개가 되면 break 합니다.
                    break
        else:
            # ABV값이 0 이상이고, Alcohol 카테고리에 속하는 재료를 선정합니다.
            count = 0
            for ing_name, score in sorted_ingredient:
                if (flavor_dic[ing_name]['ABV'] >= 0) and ('Alcohol' in category_data[ing_name]):
                    top_10_ingredient.append(ing_name)
                    count += 1
                if count == 10: # 재료가 10개가 되면 break 합니다.
                    break

        top_10_flavor = {}
        for ing_name in top_10_ingredient:
            top_10_flavor[ing_name] = {}
            for feature, value in flavor_dic[ing_name].items():
                # 몇몇 재료는 'ID' feature가 들어가 있습니다. flavor정보에 오류가 있어 보입니다.
                if feature != "ID":
                    top_10_flavor[ing_name][feature] = value

        return {"ingredients" : top_10_ingredient,
                "flavor" : top_10_flavor}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 모델에 user profile과 seed ingredient를 입력으로 받고, inference를 수행합니다.
# inference를 수행하고 나온 결과를 전달합니다.
@app.post("/predict", response_model=Recipe)
async def predict(features: Features):
    # Extract input features
    # Predict using the model
    try:
        input_features = {'ABV': features.ABV,
                          'sweet' : features.sweet,
                          'sour' : features.sour,
                          'bitter' : features.bitter,
                          'spicy' : features.spicy,
                          'herbal' : features.herbal,
                          'floral' : features.floral,
                          'fruity' : features.fruity,
                          'nutty' : features.nutty,
                          'boozy' : features.boozy,
                          'astringent' : features.astringent,
                          'umami' : features.umami,
                          'salty' : features.salty,
                          'Perceived_temperature' : features.perceived_t,
                          'creamy' : features.creamy,
                          'smoky' : features.smoky,
                          }
        seed_ingredient = features.seed
        total_amount = 200 #ml
        eval_obj = Eval(json_data, flavor_data, category_data, model, total_amount)

        recipe_length = 5
        generated_recipes = eval_obj.generate_recipe(seed_ingredient, input_features, recipe_length)
        result_recipe = {}


        for recipe, ingredients in zip(generated_recipes[0], generated_recipes[1]):
            result_recipe[recipe]= ingredients * total_amount

        user_recipe_profile = eval_obj.get_taste_log(generated_recipes)

        return {"recipe" : result_recipe,
                "profile" : user_recipe_profile}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
