from pymongo import MongoClient
from bson import ObjectId
from fastapi import FastAPI
from fastapi import Body

from datetime import datetime
import jwt
import time

client = MongoClient("mongodb://root:1234@mongo:27017/?authSource=admin") # если запущен в доекре

db = client['ShopDB']
prod_coll = db.products
users_coll = db.users
basket_coll = db.baskets

app = FastAPI()

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

# методы работы с корзинами
#===============================
@app.post("/mongo_api/basket_create", tags=["Basket object methods"])
async def basket_create(token : str = Body(...)):
    
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    
    basket_id = basket_coll.insert_one({"owner_user_id" : ObjectId(verify[1]), "time_opened" : str(datetime.now()), "basket_contents" : []}).inserted_id

    return {"basket_id" : str(basket_id)}

# общие данные о корзине
@app.post("/mongo_api/get_basket_data", tags=["Basket object methods"])
async def get_basket_data(token : str = Body(...),
                          basket_id : str = Body(...)): 
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})

    return normalise_ids(doc)

# что лежит в коризне
@app.post("/mongo_api/get_basket_contents", tags=["Basket object methods"])
async def get_products_in_basket(token : str = Body(...),
                                 basket_id : str = Body(...)): 
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})
    bask_contents_data = []
    for elm in doc["basket_contents"]:
        bask_contents_data.append({**prod_coll.find_one({"_id" : elm["product_id"]}), "amount_in_basket" : elm["amount"]} )

    return normalise_ids(bask_contents_data)

# добавить товар в корзину
@app.post("/mongo_api/basket_add_item", tags=["Basket object methods"])
async def basket_add_item(  token : str = Body(...),
                            basket_id : str = Body(...),
                            product_id : str = Body(...),
                            amount : int = Body(...)):
    
    # добавить проверку, что добавляемое количество меньше максимально доступного + 
    # вообще это должно в интерфейсе отрабатываться, где предлагается выбрать чисто от 1 до доступного кол-ва
    # доступное количество передается методом, который дает инфу по товарам
    # здесь будет только проверка при закрытии корзины

    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})
    if doc is None:
        return "BASKET NOT FOUND"
    if str(doc["owner_user_id"]) != verify[1]:
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = doc["time_closed"] if "time_closed" in doc else None
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------
    # проверка количества товара
    # ---------------------------------------
    if int(amount) <= 0:
        return "AMOUNT INVALID", str(product_id)
    avail_product_amount = prod_coll.find_one({"_id" : ObjectId(product_id)})["amount"]
    if int(amount) > int(avail_product_amount):
        return "ADDING MORE THEN AVAILABLE", str(product_id)
    # ---------------------------------------    
    # проверка нети ли этого товара уже в корзине
    # ---------------------------------------
    bask_cont = basket_coll.find_one({"_id" : ObjectId(basket_id)})["basket_contents"]
    for i in range(len(bask_cont)):
        if bask_cont[i]["product_id"] == ObjectId(product_id):
            return "ALREADY IN BASKET", str(product_id)
    # ---------------------------------------    

    # если товар уже есть в корине по идее интерфейс должен не давать случиться такой ситуации
    basket_coll.update_one({"_id" : ObjectId(basket_id)}, {"$set" : {"basket_contents" : basket_coll.find_one({"_id" : ObjectId(basket_id)})["basket_contents"] + [{"product_id" : ObjectId(product_id), "amount" : amount}]}})

    return "OK"

# поменять количество товара в корзине
@app.post("/mongo_api/basket_mod_item", tags=["Basket object methods"])
async def basket_mod_item(  token : str = Body(...),
                            basket_id : str = Body(...) ,
                            product_id : str = Body(...),
                            amount : int = Body(...)):
    
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})
    if doc is None:
        return "BASKET NOT FOUND"
    if str(doc["owner_user_id"]) != verify[1]:
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = doc["time_closed"] if "time_closed" in doc else None
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------
    # проверка количества товара
    # ---------------------------------------
    if int(amount) <= 0:
        return "AMOUNT INVALID", str(product_id)
    avail_product_amount = prod_coll.find_one({"_id" : ObjectId(product_id)})["amount"]
    if int(amount) > int(avail_product_amount):
        return "ADDING MORE THEN AVAILABLE", str(product_id)
    # ---------------------------------------    

    bask_cont = basket_coll.find_one({"_id" : ObjectId(basket_id)})["basket_contents"]
    for i in range(len(bask_cont)):
        if bask_cont[i]["product_id"] == ObjectId(product_id):
            bask_cont[i]["amount"] = amount
    print(bask_cont)
    basket_coll.update_one({"_id" : ObjectId(basket_id)}, {"$set" : {"basket_contents" : bask_cont}})

    return "OK"

# удалить товар из корзины
@app.post("/mongo_api/basket_remove_item", tags=["Basket object methods"])
async def basket_remove_item(   token : str = Body(...),
                                basket_id : str = Body(...) ,
                                product_id : str = Body(...)):
    
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})
    if doc is None:
        return "BASKET NOT FOUND"
    if str(doc["owner_user_id"]) != verify[1]:
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = doc["time_closed"] if "time_closed" in doc else None
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------

    bask_cont = basket_coll.find_one({"_id" : ObjectId(basket_id)})["basket_contents"]
    bask_cont = [elm for elm in bask_cont if str(elm["product_id"]) != str(product_id)]

    basket_coll.update_one({"_id" : ObjectId(basket_id)}, {"$set" :  {"basket_contents" : bask_cont}})

    return "OK"

# закрыть коризину (тут в теории информация должна передаваться в сервис оплаты и доставки)
@app.post("/mongo_api/basket_finalize", tags=["Basket object methods"])
async def basket_finalize(  token : str = Body(...),
                            basket_id : str = Body(...)):
    
    # указываем дату закрытия корзины и возвращаем спиок всех товаров
    
    verify = verify_user(token)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})
    if doc is None:
        return "BASKET NOT FOUND"
    if str(doc["owner_user_id"]) != verify[1]:
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = doc["time_closed"] if "time_closed" in doc else None
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------

    # проверка наличия достаточного количества товаров
    bask_cont = basket_coll.find_one({"_id" : ObjectId(basket_id)})["basket_contents"]

    for elm in bask_cont:
        amount_available = prod_coll.find_one({"_id" : ObjectId(elm["product_id"])})["amount"]
        amount_requested = elm["amount"]
        if int(amount_requested) > int(amount_available):
            
            return "REQUESTED MORE THEN AVAILABLE", str(elm["product_id"])
        # обновляем количество доступного на складе товара
        prod_coll.update_one({"_id" : ObjectId(elm["product_id"])}, {"$set" :  {"amount" : amount_available - amount_requested}})

    basket_coll.update_one({"_id" : ObjectId(basket_id)}, {"$set" :  {"time_closed" : str(datetime.now())}})

    # сделать проверку, чтобы нельзя было закрыть одну и ту же корзину много раз +
    # еще надо сделать так, чтобы при закрытии корзины число товаров в ней вычиталось из amount в товарах +
    # и добавить проверку, чтобы amount не мог стать отрициательным +
    
    # вообще получется если 2 чела набрали максимум одного и того же товара, то у того, кто попробует купить вторым не пройдет
    doc = basket_coll.find_one({"_id" : ObjectId(basket_id)})["basket_contents"]
    basket_data = {"contents_data" : [], "price" : 0}
    for elm in doc:
        prod_data = normalise_ids(prod_coll.find_one({"_id" : ObjectId(elm["product_id"])}, {"_id" : 0, "amount" : 0}))
        basket_data["contents_data"].append({"_id" : str(elm["product_id"]), 
                                             "amount" : elm["amount"], 
                                             "extra_data" : prod_data})
        basket_data["price"] += prod_data["price"] * elm["amount"]
    return basket_data