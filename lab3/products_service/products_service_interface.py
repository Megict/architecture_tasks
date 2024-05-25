from pymongo import MongoClient
from bson import ObjectId
from bson import json_util
from fastapi import FastAPI
from fastapi import Request, Body
import json

from datetime import datetime
from datetime import timedelta
import bcrypt

from pydantic import BaseModel

class UserData(BaseModel):
    user_name: str
    user_password: str
    name_first: str
    name_last: str

client = MongoClient("mongodb://root:1234@mongo:27017/?authSource=admin") # если запущен в доекре

db = client['ShopDB']
prod_coll = db.products
users_coll = db.users
basket_coll = db.baskets

app = FastAPI()

def verify_user(user_name, presented_password):
    try:
        doc = users_coll.find_one({"username" : user_name})
        if doc is None:
            # такого пользователя нету
            return "USER DOES NOT EXIST"
        user_id, user_password_hash, user_password_salt = str(doc["_id"]), doc["pword_hash"], doc["pword_salt"]
        if bcrypt.hashpw(presented_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
            return "OK", user_id
        else:
            return "WRONG PASSWORD"
    except IndexError:
        return "USER DOES NOT EXIST"

def is_iterable(elm):
    try:
        _ = iter(elm)
    except TypeError:
        return False
    return True

def normalise_ids(data):
    if type(data) == dict:
        if "_id" in data:
            data["_id"] = str(data["_id"])
        if "owner_user_id" in data:
            data["owner_user_id"] = str(data["owner_user_id"])
        if "product_id" in data:
            data["product_id"] = str(data["product_id"])
        for elm in data:
            if(type(data[elm]) == list):
                data[elm] = normalise_ids(data[elm])
        return data
    if type(data) == list:
        for i in range(len(data)):
            if "_id" in data[i]:
                data[i]["_id"] = str(data[i]["_id"])
            if "owner_user_id" in data[i]:
                data[i]["owner_user_id"] = str(data[i]["owner_user_id"])
            if "product_id" in data[i]:
                data[i]["product_id"] = str(data[i]["product_id"])
            for elm in data[i]:
                if(type(data[i][elm]) == list):
                    data[i][elm] = normalise_ids(data[i][elm])
        return data

@app.get("/mongo_api/ping")
def ping():
    return None

# методы работы с продуктами
#===============================
@app.post("/mongo_api/add_new_product", tags=["Product object methods"])
async def add_new_product(  product_name : str = Body(...),
                            product_price : int = Body(...),
                            product_amount : int = Body(...)):

    new_prod_id = prod_coll.insert_one({"name" : product_name, "price" : product_price, "amount" : product_amount}).inserted_id
    
    return {"prod_id" : str(new_prod_id)}

@app.get("/mongo_api/get_all_available_items_list", tags=["Product object methods"])
async def get_all_available_items_list():

    all_product_data = list(prod_coll.find({}))

    return normalise_ids(all_product_data)

@app.get("/mongo_api/get_product_data", tags=["Product object methods"])
async def get_product_data(product_id):
    
    product_data = list(prod_coll.find({"_id" : ObjectId(product_id)}))
    
    if len(product_data) == 0:
        return "NO SUCH PRODUCT"
    else:
        return normalise_ids(product_data[0])

@app.post("/mongo_api/change_product_data", tags=["Product object methods"])
async def add_new_product(  product_id : str = Body(...),
                            new_product_name : str = Body(None),
                            new_product_price : int = Body(None),
                            new_product_amount : int = Body(None)):
    
    q = {}

    if new_product_name is not None:
        q = {"name" : new_product_name, **q}
    if new_product_price is not None:
        q = {"price" : new_product_price, **q}
    if new_product_amount is not None:
        q = {"amount" : new_product_amount, **q}

    if q == {}:
        return "NOTHING TO UPDATE"
    prod_coll.update_one({"_id" : ObjectId(product_id)}, {"$set" : q})
    
    return "OK"
