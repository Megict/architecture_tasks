from pymongo import MongoClient
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
# client = MongoClient("mongodb://root:1234@localhost:27020/?authSource=admin")
db = client['ShopDB']
prod_coll = db.products
users_coll = db.users
basket_coll = db.baskets

app = FastAPI()

def verify_user(user_name, presented_password):
    try:
        doc = users_coll.find_one({"username" : user_name})
        user_id, user_password_hash, user_password_salt = doc["_id"], doc["pword_hash"], doc["pword_salt"]
        if bcrypt.hashpw(presented_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
            return "OK", user_id
        else:
            return "WRONG PASSWORD"
    except IndexError:
        return "USER DOES NOT EXIST"


@app.get("/mongo_api/ping")
def ping():
    return None

# методы работы с пользователями
#===============================
@app.post("/mongo_api/user_create", tags=["User object methods"])
# добавить пользователя
async def user_create(  user_name : str = Body(...) ,
                        user_password : str = Body(...),
                        name_first : str = Body('Null'),
                        name_last : str = Body('Null')
                        ):
    
    # проверка, не занято ли имя
    result_cnt = users_coll.count({"username" : user_name})
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
                        name_first : str = Body('Null'),
                        name_last : str = Body('Null')
                        ):
    # можно изменить что угодно, если данные не меняются, то надо передать старые

    # верификация по паролю
    doc = users_coll.find_one({"username" : old_user_name})
    user_id, user_password_hash, user_password_salt = doc["_id"], doc["pword_hash"], doc["pword_salt"]

    if bcrypt.hashpw(old_user_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
        # проверка, не занято ли имя
        result_cnt = users_coll.count({"username" : user_name})
        if result_cnt != 0:
            return "user name unavailable"
        # запись
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')
        users_coll.update({"_id" : user_id}, {"username" : user_name, "pword_hash" : password_hash, "pword_salt" : salt.decode('utf-8'), "name_first" : name_first, "name_last" : name_last})
        
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
    
    doc = users_coll.find_one({"username" : user_name}, {"pword_hash" : False, "pword_salt" : False})
    return doc

# возвращаем список всех корзин пользователя
@app.post("/mongo_api/produce_user_baskets", tags=["User object methods"])
async def produce_user_baskets( user_name : str = Body(...) ,
                                user_password : str = Body(...)):

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    result = basket_coll.find({"owner_user_id" : verify[1]})
    
    return [{"basket_id" : bask["_id"], "basket_owned" : bask["owner_user_id"], "basket_opened" : bask["time_opened"], "basket_closed" : bask["time_closed"], "basket_contents" : get_products_in_basket(bask[0])}  for bask in result]

# методы работы с корзинами
#===============================
@app.post("/mongo_api/basket_create", tags=["Basket object methods"])
async def basket_create(user_name : str = Body(...) ,
                        user_password : str = Body(...)):
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    basket_id = basket_coll.instert_one({"owner_user_id" : verify[1], "time_opened" : str(datetime.now()), "basket_contents" : []})

    return {"basket_id" : basket_id}

# общие данные о корзине
@app.get("/mongo_api/get_basket_data", tags=["Basket object methods"])
def get_basket_data(basket_id): 
    
    doc = basket_coll.find_one({"_id" : basket_id})

    return doc

# что лежит в коризне
@app.get("/mongo_api/get_basket_contents", tags=["Basket object methods"])
def get_products_in_basket(basket_id): 
    
    doc = basket_coll.find_one({"_id" : basket_id})
    bask_contents_data = []
    for elm in doc["basket_contents"]:
        bask_contents_data.append(prod_coll.find({"_id" : elm["product_id"]}))

    return bask_contents_data

# добавить товар в корзину
@app.post("/mongo_api/basket_add_item", tags=["Basket object methods"])
async def basket_add_item(  user_name : str = Body(...) ,
                            user_password : str = Body(...) ,
                            basket_id : int = Body(...) ,
                            product_id : int = Body(...),
                            amount : int = Body(...)):
    
    # добавить проверку, что добавляемое количество меньше максимально доступного + 
    # вообще это должно в интерфейсе отрабатываться, где предлагается выбрать чисто от 1 до доступного кол-ва
    # доступное количество передается методом, который дает инфу по товарам
    # здесь будет только проверка при закрытии корзины

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    docs = basket_coll.find({"_id" : basket_id})
    if len(docs) == 0:
        return "BASKET NOT FOUND"
    if int(docs[0]["owner_user_id"]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = docs[0]["time_closed"]
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------
    # проверка количества товара
    # ---------------------------------------
    avail_product_amount = prod_coll.find({"_id" : {product_id}})["amount"]
    if int(amount) > int(avail_product_amount):
        return "ADDING MORE THEN AVAILABLE", int(product_id)
    # ---------------------------------------    

    # если товар уже есть в корине по идее интерфейс должен не давать случиться такой ситуации
    basket_coll.update({"_id" : basket_id}, {"basket_contents" : basket_coll.find_one({"_id" : basket_id})["basket_contents"] + [{"product_id" : product_id, "amount" : amount}]})

    return "OK"

# поменять количество товара в корзине
@app.post("/mongo_api/basket_mod_item", tags=["Basket object methods"])
async def basket_mod_item(  user_name : str = Body(...) ,
                            user_password : str = Body(...) ,
                            basket_id : int = Body(...) ,
                            product_id : int = Body(...),
                            amount : int = Body(...)):
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    docs = basket_coll.find({"_id" : basket_id})
    if len(docs) == 0:
        return "BASKET NOT FOUND"
    if int(docs[0]["owner_user_id"]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = docs[0]["time_closed"]
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------
    # проверка количества товара
    # ---------------------------------------
    avail_product_amount = prod_coll.find({"_id" : {product_id}})["amount"]
    if int(amount) > int(avail_product_amount):
        return "ADDING MORE THEN AVAILABLE", int(product_id)
    # ---------------------------------------    

    bask_cont = basket_coll.find_one({"_id" : basket_id})["basket_contents"]
    for i in range(len(bask_cont)):
        if bask_cont[i]["product_id"] == product_id:
            bask_cont[i]["amount"] = amount

    basket_coll.update({"_id" : basket_id}, {"basket_contents" : bask_cont})

    return "OK"

# удалить товар из корзины
@app.post("/mongo_api/basket_remove_item", tags=["Basket object methods"])
async def basket_remove_item(   user_name : str = Body(...) ,
                                user_password : str = Body(...) ,
                                basket_id : int = Body(...) ,
                                product_id : int = Body(...)):

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    docs = basket_coll.find({"_id" : basket_id})
    if len(docs) == 0:
        return "BASKET NOT FOUND"
    if int(docs[0]["owner_user_id"]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = docs[0]["time_closed"]
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------

    bask_cont = basket_coll.find_one({"_id" : basket_id})["basket_contents"]
    bask_cont = [elm for elm in bask_cont if elm["product_id"] != product_id]

    basket_coll.update({"_id" : basket_id}, {"basket_contents" : bask_cont})

    return "OK"

# закрыть коризину (тут в теории информация должна передаваться в сервис оплаты и доставки)
@app.post("/mongo_api/basket_finalize", tags=["Basket object methods"])
async def basket_finalize(  user_name : str = Body(...) ,
                            user_password : str = Body(...) ,
                            basket_id : int = Body(...)):
    
    # указываем дату закрытия корзины и возвращаем спиок всех товаров
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины
    # проверка принадлежности корзины
    # ---------------------------------------
    docs = basket_coll.find({"_id" : basket_id})
    if len(docs) == 0:
        return "BASKET NOT FOUND"
    if int(docs[0]["owner_user_id"]) != int(verify[1]):
        return "NOT YOUR BASKET"
    # ---------------------------------------
    # проверка, не закрыта ли корзина
    # ---------------------------------------
    basket_closed_data = docs[0]["time_closed"]
    if basket_closed_data is not None:
        return "CLOSED BASKET"
    # ---------------------------------------

    # проверка наличия достаточного количества товаров
    bask_cont = basket_coll.find_one({"_id" : basket_id})["basket_contents"]

    for elm in bask_cont:
        amount_available = prod_coll.find_one({"_id" : elm["product_id"]})["amount"]
        amount_requested = elm["amount"]
        if int(amount_requested) > int(amount_available):
            
            return "REQUESTED MORE THEN AVAILABLE", int(elm["product_id"])
        # обновляем количество доступного на складе товара
        prod_coll.update({"_id" : int(elm["product_id"])}, {"amount" : amount_available - amount_requested})

    basket_coll.update({"_id" : basket_id}, {"time_colsed" : str(datetime.now())})

    # сделать проверку, чтобы нельзя было закрыть одну и ту же корзину много раз +
    # еще надо сделать так, чтобы при закрытии корзины число товаров в ней вычиталось из amount в товарах +
    # и добавить проверку, чтобы amount не мог стать отрициательным +
    
    # вообще получется если 2 чела набрали максимум одного и того же товара, то у того, кто попробует купить вторым не пройдет
    doc = basket_coll.find_one({"_id" : basket_id})["basket_contents"]
    return [{*elm, *prod_coll.find_one({"_id" : elm["product_id"]}, {"_id" : False})} for elm in doc]

# методы работы с продуктами
#===============================
@app.post("/mongo_api/add_new_product", tags=["Product object methods"])
async def add_new_product(  product_name : str = Body(...),
                            product_price : int = Body(...),
                            product_amount : int = Body(...)):

    new_prod_id = prod_coll.insert_one({"name" : product_name, "price" : product_price, "amount" : product_amount}).inserted_id
    
    return {"prod_id" : new_prod_id.ToString()}

@app.get("/mongo_api/get_all_available_items_list", tags=["Product object methods"])
async def get_all_available_items_list():

    all_product_data = prod_coll.find({}, {"_id", False})

    all_prod_list = []
    for elm in all_product_data:
        all_prod_list.append(elm)
    return json.loads(json_util.dumps(all_prod_list))

@app.get("/mongo_api/get_product_data", tags=["Product object methods"])
async def get_product_data(product_id):
    
    product_data = prod_coll.find({"_id" : myObjectId(product_id)})
    
    if len(product_data) == 0:
        return "NO SUCH PRODUCT"
    else:
        return product_data[0]

@app.post("/mongo_api/change_product_data", tags=["Product object methods"])
async def add_new_product(  product_id : int = Body(...),
                            new_product_name : str = Body(None),
                            new_product_price : int = Body(None),
                            new_product_amount : int = Body(None)):
    
    q = {}

    if new_product_name is not None:
        q += {"name" : new_product_name}
    if new_product_price is not None:
        q += {"price" : new_product_price}
    if new_product_amount is not None:
        q += {"amount" : new_product_amount}

    if q == {}:
        return "NOTHING TO UPDATE"
    prod_coll.update({"_id" : product_id}, q)
    
    return "OK"

# import yaml
# docs = app.openapi()
# with open("index.yaml", 'w') as f:
#     yaml.dump(docs, f)