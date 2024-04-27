### connect mongodb
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json

# Replace the placeholder with your Atlas connection string
# uri = "mongodb+srv://user0:<password>@cluster0.apx21d0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
uri = "mongodb://localhost:27017"

# Set the Stable API version when creating a new client
client = MongoClient(uri, server_api=ServerApi('1'))
db_name = "data-engineering"
drinks = "drinks"
feedbacks = "feedbacks"

def add_drinks(new_drinks):                 
    try:
        de = client[db_name]
        drinks = de[drinks]
        result = drinks.insert_many(new_drinks)
        return result
    except Exception as e:
        print(e)
# with open("image0001.json", "r", encoding="utf-8") as f:
#     test = json.load(f)
#     result = add_new_drinks([test])
#     print(result)

def find_drink_by_name(name):
    try:
        de = client[db_name]
        drinks = de[drinks]
        result = drinks.find_one({"name": name})
        return result
    except Exception as e:
        print(e)

def add_feedback(feedback):
    try:
        de = client[db_name]
        feedbacks = de[feedbacks]
        result = feedback.insert_one(feedback)
        return result
    except Exception as e:
        print(e)