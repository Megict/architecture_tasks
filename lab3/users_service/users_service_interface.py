from pymongo import MongoClient
from bson import ObjectId
from bson import json_util
from fastapi import FastAPI
from fastapi import Request, Body
import requests
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

@app.post("/mongo_api/user_change", tags=["User object methods"])
async def user_change(  old_user_name : str = Body(...),
                        old_user_password : str = Body(...),
                        user_name : str = Body(...),
                        user_password : str = Body(...),
                        name_first : str = Body(None),
                        name_last : str = Body(None)
                        ):
    # можно изменить что угодно, если данные не меняются, то надо передать старые

    # верификация по паролю
    doc = users_coll.find_one({"username" : old_user_name})
    user_id, user_password_hash, user_password_salt = doc["_id"], doc["pword_hash"], doc["pword_salt"]

    if bcrypt.hashpw(old_user_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
        # проверка, не занято ли имя
        result_cnt = len(list(users_coll.find({"username" : user_name})))
        if result_cnt != 0:
            return "user name unavailable"
        # запись
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')
        users_coll.update_one({"_id" : user_id}, {"$set": {"username" : user_name, "pword_hash" : password_hash, "pword_salt" : salt.decode('utf-8'), "name_first" : name_first, "name_last" : name_last}})
        
        return "OK"
    else:
        # неверный пароль, ничего не делаем
        return "WRONG PASSWORD"

# возвращаем данные по пользователю, пароль и имя которого предоставлено
@app.post("/mongo_api/produce_user_data", tags=["User object methods"])
async def produce_user_data(user_name : str = Body(...) ,
                            user_password : str = Body(...)):

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    doc = users_coll.find_one({"username" : user_name}, {"pword_hash" : 0, "pword_salt" : 0})
    return normalise_ids(doc)

# возвращаем список всех корзин пользователя
@app.post("/mongo_api/produce_user_baskets", tags=["User object methods"])
async def produce_user_baskets( user_name : str = Body(...) ,
                                user_password : str = Body(...)):

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    result = basket_coll.find({"owner_user_id" : ObjectId(verify[1])})

    return [{"basket_id" : str(bask["_id"]), "basket_owned" : str(bask["owner_user_id"]), "basket_opened" : bask["time_opened"], "basket_closed" : bask["time_closed"] if "time_closed" in bask else None, "basket_contents" : json.loads(requests.get("http://basket_service:8000/mongo_api/get_basket_contents", params = {"basket_id" : str(bask["_id"])}).text)}  for bask in result]