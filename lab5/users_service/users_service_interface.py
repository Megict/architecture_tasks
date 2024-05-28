from pymongo import MongoClient
from bson import ObjectId
from fastapi import FastAPI
from fastapi import Body
import requests
import json

import time
import bcrypt
import jwt
import redis

from pydantic import BaseModel

class UserData(BaseModel):
    user_name: str
    user_password: str
    name_first: str
    name_last: str

client = MongoClient("mongodb://root:1234@mongo:27017/?authSource=admin") # если запущен в доекре
# client = MongoClient("mongodb://root:1234@localhost:27020/?authSource=admin") 

db = client['ShopDB']
prod_coll = db.products
users_coll = db.users
basket_coll = db.baskets

app = FastAPI()

redis_client = redis.Redis(host="redis")
use_cache = True

def authenticate_user(user_name, presented_password):
    try:
        doc = users_coll.find_one({"username" : user_name})
        if doc is None:
            # такого пользователя нету
            return "USER DOES NOT EXIST"
        user_id, user_password_hash, user_password_salt = str(doc["_id"]), doc["pword_hash"], doc["pword_salt"]
        if bcrypt.hashpw(presented_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
            # пароль верен
            encoded_jwt = jwt.encode({"uid": user_id, "ist" : time.time()}, "1234", algorithm="HS256")
            print(type(encoded_jwt))
            return "OK", encoded_jwt
        else:
            return "WRONG PASSWORD"
    except IndexError:
        return "USER DOES NOT EXIST"
    
def verify_user(presented_jwt):
    try:
        data = jwt.decode(presented_jwt, "1234", algorithms=["HS256"])
        if float(data["ist"]) + 600 < time.time():
            return "TOKEN EXPIRED"
        return "OK", data["uid"]
    except jwt.exceptions.DecodeError:
        return "TOKEN INVALID"

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

@app.get("/mongo_api/cache_switch")
def cache_switch():
    global use_cache
    try:
        use_cache = not use_cache
    except UnboundLocalError:
        use_cache = True
    return "status after switch: " + str(use_cache)

# методы работы с пользователями
#===============================
@app.post("/mongo_api/user_create", tags=["User object methods"])
# добавить пользователя
async def user_create(  user_name : str = Body(...) ,
                        user_password : str = Body(...),
                        name_first : str = Body(None),
                        name_last : str = Body(None)
                        ):
    
    # проверка, не занято ли имя
    result_cnt = len(list(users_coll.find({"username" : user_name})))
    if result_cnt != 0:
        return "user name unavailable"
    # запись

    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')

    users_coll.insert_one({"username" : user_name, "pword_hash" : password_hash, "pword_salt" : salt.decode('utf-8'), "name_first" : name_first, "name_last" : name_last})

    return None

# возвращаем данные по пользователю, пароль и имя которого предоставлено
@app.post("/mongo_api/authenticate_user", tags=["User object methods"])
async def authorise_user(user_name : str = Body(...) ,
                         user_password : str = Body(...)):

    token = authenticate_user(user_name, user_password)
    if token[0] != "OK":
        return token
    
    return token[1]

@app.post("/mongo_api/user_change", tags=["User object methods"])
async def user_change(  token : str = Body(...),
                        user_name : str = Body(...),
                        user_password : str = Body(...),
                        name_first : str = Body(None),
                        name_last : str = Body(None)
                        ):
    # можно изменить что угодно, если данные не меняются, то надо передать старые

    verify = verify_user(token)
    if verify[0] != "OK":
        return verify

    result_elm = users_coll.find_one({"username" : user_name})
    if result_elm is None or ObjectId(result_elm["_id"]) == ObjectId(verify[1]):
        pass
    else:
        return "user name unavailable"
    # запись
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')
    users_coll.update_one({"_id" : ObjectId(verify[1])}, {"$set": {"username" : user_name, "pword_hash" : password_hash, "pword_salt" : salt.decode('utf-8'), "name_first" : name_first, "name_last" : name_last}})
    
    return "OK"

# возвращаем данные по пользователю, пароль и имя которого предоставлено
@app.post("/mongo_api/produce_user_data", tags=["User object methods"])
async def produce_user_data(token : str = Body(...)):
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    
    if use_cache:
        cached_data = redis_client.get(token + "_produce_user_data") # берем данные из кэша
        if cached_data is not None:
            print("using redis cache")
            return json.loads(cached_data)
    
    doc = normalise_ids(users_coll.find_one({"_id" : ObjectId(verify[1])}, {"pword_hash" : 0, "pword_salt" : 0}))
    if use_cache:
        print("caching data")
        redis_client.set(token + "_produce_user_data", json.dumps(doc), ex = 60) # записываем данные в кэш
    return normalise_ids(doc)

# возвращаем список всех корзин пользователя
@app.post("/mongo_api/produce_user_baskets", tags=["User object methods"])
async def produce_user_baskets(token : str = Body(...)):

    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    
    if use_cache:
        cached_data = redis_client.get(token + "_produce_user_baskets") # берем данные из кэша
        if cached_data is not None:
            print("using redis cache")
            return json.loads(cached_data)
    
    result = basket_coll.find({"owner_user_id" : ObjectId(verify[1])})

    res = [{"basket_id" : str(bask["_id"]), "basket_owned" : str(bask["owner_user_id"]), "basket_opened" : bask["time_opened"], "basket_closed" : bask["time_closed"] if "time_closed" in bask else None, "basket_contents" : json.loads(requests.post("http://basket_service:8000/mongo_api/get_basket_contents", json = {"basket_id" : str(bask["_id"]), "token" : token}).text)}  for bask in result]

    if use_cache:
        print("caching data")
        redis_client.set(token + "_produce_user_baskets", json.dumps(res), ex = 60) # записываем данные в кэш
    return res