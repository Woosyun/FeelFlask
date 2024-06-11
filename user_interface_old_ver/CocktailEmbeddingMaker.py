import numpy as np
import pandas as pd
import random
import tensorflow as tf
import wandb


class CocktailEmbeddingMaker:
    def __init__(self, json_data, flavor_data,category_data, total_amount=200):
        self.cocktail_info = json_data['cocktail_info']
        self.flavor_data = flavor_data
        self.total_amount = total_amount
        self.max_recipe_length=10
        self.category_data = category_data
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
        # print(f"Total Amount: {total_amount} , Recipe: {recipe}")
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
                # print(f"[get_taste_info]recipe_taste_weights : {recipe_taste_weights}")
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
    
class Inference(CocktailEmbeddingMaker):
    def __init__(self,json_data, flavor_data,model, total_amount=200):
        super().__init__(json_data, flavor_data, total_amount=200)
        self.model = model
        
    def test_case_with_random_seed(self, test_user):
        seed_ingredient=random.choice(list(self.ingredient_ids.keys()))
        generated_recipes = self.generate_recipe(seed_ingredient,test_user)
        recipe_profile=self.get_taste_log(generated_recipes)
        return recipe_profile
    
    def test_case_with_user_seed(self, test_user, seed_ingredient):
        generated_recipes = self.generate_recipe(seed_ingredient,test_user)
        recipe_profile=self.get_taste_log(generated_recipes)
        return recipe_profile
    
    def get_taste_log(self,generated_recipe):
        recipe = {}
        for item, quantity_ratio in zip(generated_recipe[0], generated_recipe[1]):
            recipe[item] = quantity_ratio * self.total_amount
            #재료-양 완성 
        #레시피의 맛 프로파일 생성
        recipe_taste = self.get_taste_info(recipe)
        return recipe_taste
    
    def get_taste_info(self,cocktail_recipe):
        recipe_taste_weights = None
        for ingredient in cocktail_recipe.keys():
            if ingredient not in self.ingredient_ids:
                print(f"Ingredient '{ingredient}' not found in ingredient_ids")
            else:
                recipe_taste_weights = self.calculate_recipe_taste_weights(cocktail_recipe)
                recipe_taste_weights.pop('ID')
            return recipe_taste_weights
        
    def generate_recipe(self, seed_ingredient, user_preference, max_length=10):
        generated_recipe = [seed_ingredient]
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
    
    
class Eval(CocktailEmbeddingMaker):
    
    def __init__(self,json_data, flavor_data,category_data,model, total_amount=200):
        super().__init__(json_data, flavor_data,category_data, total_amount=200)
        self.model = model
        
    def evaluate_model(self,model, test_user_list, num_recipes=100):
        self.model = model
        similarity_list= []
        diversity_list = []
        abv_match_list = []
        taste_match_list = []
        recipe_profile_list=[]
        for user in test_user_list:
            # def generate_recipe(self, seed_ingredient, user_preference, max_length=10):
            seed_ingredient=random.choice(list(self.ingredient_ids.keys()))
            generated_recipes = self.generate_recipe(seed_ingredient,user)
            print(generated_recipes)
            recipe_profile=self.get_taste_log(generated_recipes)
            recipe_profile_list.append(recipe_profile)
            s = self.evaluate_similarity(generated_recipes)
            d = self.evaluate_diversity(generated_recipes)
            a = self.evaluate_abv_match(generated_recipes, user)
            t = self.evaluate_taste_match(generated_recipes, user)
            print(f"s : {s}, d : {d}, a : {a}, t : {t}")
            similarity_list.append(s)
            diversity_list.append(d)
            abv_match_list.append(a)
            taste_match_list.append(t)

        similarity = np.mean(similarity_list)
        diversity = np.mean(diversity_list)
        abv_match = np.mean(abv_match_list)
        taste_match = np.mean(taste_match_list)
        evaluation_metrics = {
            'similarity': similarity,
            'diversity': diversity,
            'abv_match': abv_match,
            'taste_match': taste_match
        }
        
        return evaluation_metrics,recipe_profile_list
    
    
    def evaluate_similarity(self, generated_recipe):
        
        
        recipe_dict = {}
        for item, quantity_ratio in zip(generated_recipe[0], generated_recipe[1]):
            recipe_dict[item] = quantity_ratio * self.total_amount
        # 벡터 생성 함수
        def create_vector(recipe, all_ingredients):
            return np.array([recipe.get(ing, 0) for ing in all_ingredients])

        # 모든 재료 목록 생성
        all_ingredients = set(recipe_dict.keys())
        for cocktail in self.cocktail_info:
            all_ingredients.update(cocktail['recipe'].keys())

        generated_vector = create_vector(recipe_dict, all_ingredients)

        max_similarity = 0
        for cocktail in self.cocktail_info:
            origin_vector = create_vector(cocktail['recipe'], all_ingredients)

            # 코사인 유사도 계산
            dot_product = np.dot(generated_vector, origin_vector)
            norm_product = np.linalg.norm(generated_vector) * np.linalg.norm(origin_vector)
            similarity = dot_product / norm_product if norm_product else 0
            max_similarity = max(max_similarity, similarity)

        return max_similarity

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
        recipe_abv = self.calculate_recipe_abv(generated_recipes[0], generated_recipes[1])

        if user_preference['ABV'] == 0:
            return 1 if recipe_abv == 0 else 0  # 사용자가 알코올을 선호하지 않으면, 레시피도 0%여야 완벽한 일치

        abv_diff = abs(recipe_abv - user_preference['ABV'])
        normalized_abv_diff = abv_diff / (user_preference['ABV'] + 0.1)  # 0.1을 더해 분모가 0이 되는 것을 방지
        abv_match = max(0, 1 - normalized_abv_diff)  # 음수 값 방지와 0-1 범위 보장

        return abv_match

    def evaluate_taste_match(self, generated_recipe, user_preference):
        # 레시피의 맛 프로파일 일치도 계산 로직 구현
        taste_match_scores = []
        recipe = {}
        for item, quantity_ratio in zip(generated_recipe[0], generated_recipe[1]):
            recipe[item] = quantity_ratio * self.total_amount
            #재료-양 완성 
        #레시피의 맛 프로파일 생성
        recipe_taste = self.get_taste_info(recipe)
        # print("Recipe Taste Profile:", recipe_taste)
        #생성 레시피 맛 프로파일과 사용자 선호도 간의 맛 일치도 계산
        taste_differences = []
        for taste, user_score in user_preference.items():
            
            if taste!='ABV' and taste in recipe_taste:
                recipe_score = recipe_taste[taste]
                # 각 맛 특성별 점수 차이의 절대값 계산
                difference = abs(recipe_score - user_score)
                # 차이를 100으로 나누어 정규화
                normalized_difference = difference / 100
                taste_differences.append(normalized_difference)
            # 평균 일치도 계산 (1에서 정규화된 차이의 평균을 뺀 값)
        if taste_differences:
            average_match = 1 - np.mean(taste_differences)
        else:
            average_match = 0  # 레시피에 맛 특성 정보가 없을 경우

        return average_match
    
    def get_taste_log(self,generated_recipe):
        recipe = {}
        for item, quantity_ratio in zip(generated_recipe[0], generated_recipe[1]):
            recipe[item] = quantity_ratio * self.total_amount
            #재료-양 완성 
        #레시피의 맛 프로파일 생성
        recipe_taste = self.get_taste_info(recipe)
        return recipe_taste
    def get_ingredient_category(self,ingredient_name):
        ingredient_category = self.category_data[ingredient_name][0]
        return ingredient_category
    
    def calculate_recipe_taste_score(self, recipe, quantities, user_preference):
        recipe_taste_score = 0
        for ingredient, quantity in zip(recipe, quantities):
            ingredient_taste_score = self.get_ingredient_taste_score(ingredient, user_preference)
            recipe_taste_score += ingredient_taste_score * quantity
        
        recipe_taste_score /= len(recipe)  # 재료 개수로 나누어 평균 점수 계산
        return recipe_taste_score
    
    def generate_recipe(self, seed_ingredient, user_preference, max_length=10):
        #TODO : 가니시 고려해야함 
        #TODO : 높은 도수의 음료는 한두가지로 제한해야함
        generated_recipe = [seed_ingredient]
        generated_quantities = []
        high_abv_count = 0
        max_high_abv = 2
        total_prob = 0
        max_prob_sum = 1.5
        while total_prob < max_prob_sum:
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
                # 재료의 카테고리를 고려하는 후처리
                category = self.get_ingredient_category(ingredient_name)

                if category in ['Alcohol']:
                    if high_abv_count >= max_high_abv:
                        probabilities[ingredient_id] *= 0.1  # 높은 도수 음료 제한
                    else:
                        high_abv_count += 1
                elif category in ['Mixer'] and user_preference['ABV']==0:
                    probabilities[ingredient_id] *= 1.5  # 무알콜 음료에는 Mixer 선호    
                # elif category in ['Condiment']:
                #     probabilities[ingredient_id] *= 10  # 과일이나 향신료, Mixer 선호
                probabilities[ingredient_id] *= ingredient_taste_score * abv_score

            sum_prob = sum(probabilities)
            normalized_prob = [prob / sum_prob for prob in probabilities]
            next_ingredient_id = np.argmax(normalized_prob)

            next_ingredient = list(self.ingredient_ids.keys())[list(self.ingredient_ids.values()).index(next_ingredient_id)]
            generated_recipe.append(next_ingredient)

            total_prob += normalized_prob[next_ingredient_id]
            if len(generated_recipe)>=max_length:
                break
        # 레시피 도수 계산 및 재료 양 조정
        target_abv = user_preference['ABV']
        quantities = self.adjust_ingredient_quantities(generated_recipe, target_abv,user_preference)
        return generated_recipe, quantities
        
        #TODO : taste고려해야함 
    def adjust_ingredient_quantities(self, recipe, target_abv, user_preference, max_iterations=100):
        quantities = [1] * len(recipe)  # 초기 재료 양 설정
        total_amount = len(recipe)
        print(f"user_preference : {user_preference}")
        for _ in range(max_iterations):
            recipe_abv = self.calculate_recipe_abv(recipe, quantities)
            recipe_taste_score = self.calculate_recipe_taste_score(recipe, quantities, user_preference)

            if abs(recipe_abv - target_abv) < 0.5 and recipe_taste_score >= 0.8:  # 목표 도수와의 차이가 0.5 미만이고 사용자 선호도 점수가 0.8 이상이면 종료
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

            # 사용자 선호도에 따라 재료 양 조정
            for i, ingredient in enumerate(recipe):
                ingredient_taste_score = self.get_ingredient_taste_score(ingredient, user_preference)
                if ingredient_taste_score < 0.5:
                    quantities[i] *= 0.9  # 선호도가 낮은 재료의 양을 감소
                    total_amount -= quantities[i] * 0.1
                elif ingredient_taste_score > 0.8:
                    quantities[i] *= 1.1  # 선호도가 높은 재료의 양을 증가
                    total_amount += quantities[i] * 0.1
            # print(f"Recipe ABV: {recipe_abv}, Recipe Taste Score: {recipe_taste_score}")
        # 총량 대비 비율로 정규화
        quantities = [q / total_amount for q in quantities]

        return quantities
    def get_ingredient_abv(self, ingredient):
        ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient), None)
        return ingredient_info['ABV'] if ingredient_info else 0

    def get_ingredient_taste_score(self, ingredient_name, user_preference):
        ingredient_info = next((item for item in self.flavor_data if item["name"] == ingredient_name), None)

        if ingredient_info:
            # ABV 점수 계산
            abv_diff = abs(ingredient_info['ABV'] - user_preference['ABV'])
            #abv max값은 75.5
            abv_score = 1 - (abv_diff / 75.5)  # 0~1 범위로 정규화

            # 맛 점수 계산
            taste_scores = []
            for taste in user_preference:
                if taste != 'ABV' and taste != 'abv_min' and taste != 'abv_max' and taste != 'user_id':
                    ingredient_taste = ingredient_info[taste] / 100
                    user_taste = user_preference[taste] / 100
                    taste_score = 1 - abs(ingredient_taste - user_taste)  # 0~1 범위로 정규화
                    taste_scores.append(taste_score)
            
            taste_score = sum(taste_scores) / len(taste_scores)  # 맛 점수들의 평균

            # 가중 평균 계산
            taste_weight = 0.7
            abv_weight = 0.3
            weighted_score = taste_weight * taste_score + abv_weight * abv_score

            return weighted_score
        else:
            print(f"there is no ingredient!:{ingredient_info}")
            return 0.0  # 재료 정보가 없는 경우 0 반환
            

