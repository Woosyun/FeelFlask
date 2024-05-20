import numpy as np
import pandas as pd
import random
import tensorflow as tf
class CocktailEmbeddingMaker:
    def __init__(self, json_data, flavor_data, total_amount=200):
        self.cocktail_info = json_data['cocktail_info']
        self.flavor_data = flavor_data
        self.total_amount = total_amount
        self.max_recipe_length=10
        self.init()

    def normalize_string(self, name):
        return name.replace('\\"', '"').replace("\\'", "'")

    def init(self):
        ingredient_ids = {}
        for idx, item in enumerate(self.flavor_data):
            item['ID'] = idx
            normalized_name = self.normalize_string(item['name'])
            ingredient_ids[normalized_name] = idx

        self.ingredient_ids = ingredient_ids
        self.num_ingredients = len(self.flavor_data)
        self.embedding_dim = 64

    def create_ingredient_embedding_matrix(self):
        ingredient_embedding_matrix = np.zeros((self.num_ingredients, len(self.flavor_data[0]) - 1))
        
        for ingredient_dict in self.flavor_data:
            ingredient_name = ingredient_dict['name']
            if ingredient_name in self.ingredient_ids:
                ingredient_id = self.ingredient_ids[ingredient_name]
                ingredient_embedding = [ingredient_dict[flavor] for flavor in ingredient_dict if flavor != 'name']
                ingredient_embedding_matrix[ingredient_id] = ingredient_embedding
        
        return ingredient_embedding_matrix
    def create_recipe_embedding_1(self, recipe):
        embedding_matrix = np.random.rand(self.num_ingredients, self.embedding_dim)
        total_amount = sum(recipe.values())
        normalized_amount = {ingredient: amount / total_amount for ingredient, amount in recipe.items()}
        weighted_embeddings = []
        for ingredient, amount in normalized_amount.items():
            normalized_ingredient = self.normalize_string(ingredient)
            if normalized_ingredient not in self.ingredient_ids:
                raise KeyError(f"Ingredient '{normalized_ingredient}' not found in ingredient_ids")
            ingredient_id = self.ingredient_ids[normalized_ingredient]
            ingredient_embedding = embedding_matrix[ingredient_id]
            weighted_embedding = ingredient_embedding * amount
            weighted_embeddings.append(weighted_embedding)
        recipe_embedding = np.sum(weighted_embeddings, axis=0)
        return recipe_embedding
    def create_recipe_embedding_2(self, recipe):
        ingredient_embedding_matrix = self.create_ingredient_embedding_matrix()
        
        total_amount = sum(recipe.values())
        normalized_amount = {ingredient: amount / total_amount for ingredient, amount in recipe.items()}
        
        weighted_embeddings = []
        for ingredient, amount in normalized_amount.items():
            normalized_ingredient = self.normalize_string(ingredient)
            if normalized_ingredient not in self.ingredient_ids:
                raise KeyError(f"Ingredient '{normalized_ingredient}' not found in ingredient_ids")
            ingredient_id = self.ingredient_ids[normalized_ingredient]
            ingredient_embedding = ingredient_embedding_matrix[ingredient_id]
            weighted_embedding = ingredient_embedding * amount
            weighted_embeddings.append(weighted_embedding)
        
        recipe_embedding = np.sum(weighted_embeddings, axis=0)
        return recipe_embedding
    


    def create_recipe_embedding_list(self):
        recipe_embeddings = dict()
        for cocktail in self.cocktail_info:
            name = cocktail['cocktail_name']
            recipe = cocktail['recipe']
            recipe_embedding = self.create_recipe_embedding_2(recipe)
            recipe_embeddings[name] = {'recipe_embedding': recipe_embedding}
        return recipe_embeddings
    
    def calculate_recipe_taste_weights(self, recipe):
        recipe_ingredients = [d for d in self.flavor_data if d['name'] in list(recipe.keys())]
        total_amount = sum(recipe.values())
        ingredient_ratios = {ingredient: amount / total_amount for ingredient, amount in recipe.items()}
        recipe_taste_weights = {}
        for ingredient, ratio in ingredient_ratios.items():
            ingredient_dict = next((d for d in recipe_ingredients if d['name'] == ingredient), None)
            if ingredient_dict:
                for taste, weight in ingredient_dict.items():
                    if taste != 'name':
                        recipe_taste_weights[taste] = recipe_taste_weights.get(taste, 0) + weight * ratio
        return recipe_taste_weights

    def create_taste_embedding_list(self):
        taste_embeddings = dict()
        for cocktail in self.cocktail_info:
            name = cocktail['cocktail_name']
            recipe = cocktail['recipe']
            recipe_taste_weights = self.calculate_recipe_taste_weights(recipe)
            taste_embeddings[name] = {'taste_embedding': np.array(list(recipe_taste_weights.values()))}
        return taste_embeddings
    def create_taste_embedding_pd(self):
        taste = dict()
        taste_embeddings = dict()
        for cocktail in self.cocktail_info:
            name = cocktail['cocktail_name']
            recipe = cocktail['recipe']
            recipe_taste_weights = self.calculate_recipe_taste_weights(recipe)
            taste[name] = np.array(list(recipe_taste_weights.values()))

        # 칵테일 이름과 특성 리스트 정의
        cocktail_names = list(taste_embeddings.keys())
        attributes = ['ABV', 'boozy', 'sweet', 'sour', 'bitter', 'umami', 'salty', 'astringent', 'Perceived_temperature', 'spicy', 'herbal', 'floral', 'fruity', 'nutty', 'creamy', 'smoky']
        
        # 데이터프레임 생성
        taste_embeddings = pd.DataFrame.from_dict(taste, orient='index', columns=attributes)
        return taste_embeddings
    def get_taste_info(self,cocktail_recipe):

        for ingredient in cocktail_recipe.keys():
            if ingredient not in self.ingredient_ids:
                print(f"Ingredient '{ingredient}' not found in ingredient_ids")
            else:
                recipe_taste_weights = self.calculate_recipe_taste_weights(cocktail_recipe)
                recipe_taste_weights.pop('ID')
                return recipe_taste_weights
    def create_combined_embedding_list(self):
        recipe_embeddings = self.create_recipe_embedding_list()
        taste_embeddings = self.create_taste_embedding_list()

        combined_embeddings = {}
        for name in recipe_embeddings.keys():
            combined_embeddings[name] = {
                'recipe_embedding': recipe_embeddings[name]['recipe_embedding'],
                'taste_embedding': taste_embeddings[name]['taste_embedding']
            }

        return combined_embeddings
    def calculate_recipe_abv(self, recipe, quantities):
        total_amount = sum(quantities)
        total_abv = 0
        for ingredient, quantity in zip(recipe, quantities):
            ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient), None)
            if ingredient_info:
                total_abv += ingredient_info['ABV'] * (quantity / total_amount)
        return total_abv
class Eval(CocktailEmbeddingMaker):
    def __init__(self,json_data, flavor_data, total_amount=200):
        super().__init__(json_data, flavor_data, total_amount=200)
        self.model = None
    def evaluate_model(self,model, test_user_list, num_recipes=100):
        self.model = model
        for user in test_user_list:
            # def generate_recipe(self, seed_ingredient, user_preference, max_length=10):
            seed_ingredient=random.choice(list(self.ingredient_ids.keys()))
            generated_recipes = self.generate_recipe(seed_ingredient,user)
        
            similarity = self.evaluate_similarity(generated_recipes)
            diversity = self.evaluate_diversity(generated_recipes)
            abv_match = self.evaluate_abv_match(generated_recipes, user)
            taste_match = self.evaluate_taste_match(generated_recipes, user)
        
            evaluation_metrics = {
                'similarity': similarity,
                'diversity': diversity,
                'abv_match': abv_match,
                'taste_match': taste_match
            }
        
        return evaluation_metrics
    def evaluate_similarity(self, generated_recipes):
        # 생성된 레시피와 원본 레시피 간의 유사도 계산
        similarity_scores = []
        for generated_recipe in generated_recipes:
            max_similarity = 0
            for origin_recipe in self.cocktail_info:
                common_ingredients = set(generated_recipe).intersection(origin_recipe)
                similarity = len(common_ingredients) / len(set(generated_recipe + list(origin_recipe.keys())))
                max_similarity = max(max_similarity, similarity)
            similarity_scores.append(max_similarity)
        avg_similarity = np.mean(similarity_scores)
        return avg_similarity

    def evaluate_diversity(self, generated_recipes):
        # 생성된 레시피와 원본 레시피 간의 다양성 계산
        ingredient_counts = {}
        for origin_recipe in self.cocktail_info:
            for ingredient in origin_recipe:
                if ingredient not in ingredient_counts:
                    ingredient_counts[ingredient] = 0
                ingredient_counts[ingredient] += 1
        
        for generated_recipe in generated_recipes:
            for ingredient in generated_recipe:
                if ingredient not in ingredient_counts:
                    ingredient_counts[ingredient] = 0
                ingredient_counts[ingredient] += 1
        
        total_ingredients = sum(ingredient_counts.values())
        ingredient_probs = [count / total_ingredients for count in ingredient_counts.values()]
        diversity = 1 - np.sum(np.square(ingredient_probs))
        return diversity

    def evaluate_abv_match(self, generated_recipes, user_preference):
        # 레시피의 도수 일치도 계산 로직 구현
        abv_diffs = []
        recipe_abv = self.calculate_recipe_abv(generated_recipes[0],generated_recipes[1])
        # print(recipe_abv)
        abv_diff = abs(recipe_abv - user_preference['ABV'])
        abv_diffs.append(abv_diff)
        avg_abv_diff = np.mean(abv_diffs)
        abv_match = 1 - avg_abv_diff / user_preference['ABV']
        return abv_match

    def evaluate_taste_match(self, generated_recipe, user_preference):
        # 레시피의 맛 프로파일 일치도 계산 로직 구현
        taste_match_scores = []
        recipe = {}
        for item, quantity_ratio in zip(generated_recipe[0], generated_recipe[1]):
            recipe[item] = quantity_ratio * self.total_amount
        recipe_taste = self.get_taste_info(recipe)
        
        # 사용자 선호도의 총 가중치 계산
        total_weight = sum(weight for taste, weight in user_preference.items() if taste != 'ABV' and taste != 'user_id' and taste != 'ID')
        
        # 맛 특성 일치도 점수 계산
        taste_score = 0
        for taste, weight in user_preference.items():
            if (taste != 'ABV' and taste != 'user_id' and taste != 'ID') and taste in recipe_taste:
                taste_score += recipe_taste[taste] * weight
        
        # 일치도 점수 정규화
        if total_weight > 0:
            normalized_taste_score = (taste_score / total_weight) * 100
        else:
            normalized_taste_score = 0
        
        taste_match_scores.append(normalized_taste_score)
        avg_taste_match = np.mean(taste_match_scores)
        return avg_taste_match
    def generate_recipe(self, seed_ingredient, user_preference, max_length=10):
        generated_recipe = [seed_ingredient]
        generated_quantities = []

        for _ in range(max_length - 1):
            sequence = [self.ingredient_ids[self.normalize_string(ingredient)] for ingredient in generated_recipe]
            sequence = tf.keras.preprocessing.sequence.pad_sequences([sequence], maxlen=self.max_recipe_length)

            probabilities = self.model.predict(sequence)[0]
            probabilities[sequence[0]] = 0  # 중복 재료 제거

            # 사용자 선호도를 반영하여 재료 선택 확률 조정
            for ingredient_id, prob in enumerate(probabilities):
                ingredient_name = list(self.ingredient_ids.keys())[list(self.ingredient_ids.values()).index(ingredient_id)]
                ingredient_taste_score = self.get_ingredient_taste_score(ingredient_name, user_preference)
                ingredient_abv = self.get_ingredient_abv(ingredient_name)
                abv_diff = abs(ingredient_abv - user_preference['ABV'])
                abv_score = 1 / (1 + abv_diff)  # 도수 차이가 작을수록 높은 점수
                probabilities[ingredient_id] *= ingredient_taste_score * abv_score

            next_ingredient_id = np.argmax(probabilities)
            next_ingredient = list(self.ingredient_ids.keys())[list(self.ingredient_ids.values()).index(next_ingredient_id)]
            generated_recipe.append(next_ingredient)

        # 레시피 도수 계산 및 재료 양 조정
        target_abv = user_preference['ABV']
        quantities = self.adjust_ingredient_quantities(generated_recipe, target_abv)
        return generated_recipe, quantities
    def adjust_ingredient_quantities(self, recipe, target_abv, max_iterations=100):
        quantities = [1] * len(recipe)  # 초기 재료 양 설정
        total_amount = len(recipe)

        for _ in range(max_iterations):
            recipe_abv = self.calculate_recipe_abv(recipe, quantities)

            if abs(recipe_abv - target_abv) < 0.5:  # 목표 도수와의 차이가 0.5 미만이면 종료
                break

            # 도수 차이에 따라 재료 양 조정
            if recipe_abv < target_abv:
                # 알코올 함량이 높은 재료의 양을 증가
                for i, ingredient in enumerate(recipe):
                    ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient), None)
                    if ingredient_info and ingredient_info['ABV'] > 0:
                        quantities[i] += 0.1
                        total_amount += 0.1
            else:
                # 알코올 함량이 낮은 재료의 양을 증가
                for i, ingredient in enumerate(recipe):
                    ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient), None)
                    if ingredient_info and ingredient_info['ABV'] == 0:
                        quantities[i] += 0.1
                        total_amount += 0.1

        # 총량 대비 비율로 정규화
        quantities = [q / total_amount for q in quantities]

        return quantities
    def get_ingredient_abv(self, ingredient):
        ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient), None)
        return ingredient_info['ABV'] if ingredient_info else 0

    def get_ingredient_taste_score(self, ingredient_name, user_preference):
        #ABV를 제외한 맛 특성 점수를 0~1사이로 정규화 함
        ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient_name), None)

        if ingredient_info:
            taste_scores = {taste: ingredient_info[taste] / 100 for taste in user_preference if (taste != 'ABV' and taste != 'abv_min' and taste != 'abv_max' and taste !='user_id')}
            abv_score = ingredient_info['ABV'] * user_preference['ABV']
            taste_score = sum(taste_scores[taste] * user_preference[taste] for taste in taste_scores)
            return taste_score * abv_score
        else:
            return 1.0
            

