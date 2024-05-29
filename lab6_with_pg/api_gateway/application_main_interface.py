from pymongo import MongoClient
from fastapi import HTTPException
from fastapi import FastAPI
from fastapi import Body
import json
import requests

from circuitbreaker import circuit
from circuitbreaker import CircuitBreakerMonitor
from circuitbreaker import CircuitBreaker

client = MongoClient("mongodb://root:1234@mongo:27017/?authSource=admin") # если запущен в доекре

db = client['ShopDB']
prod_coll = db.products
users_coll = db.users
basket_coll = db.baskets

app = FastAPI()

async def fallback(*args, **kwargs):
    raise HTTPException(status_code= 503, detail= "blocked by circit breaker")

class CircitBreakerForServices(CircuitBreaker):
    FAILURE_THRESHOLD = 2
    RECOVERY_TIMEOUT = 60
    FALLBACK_FUNCTION = fallback

users_cb = CircitBreakerForServices()
baskets_cb = CircitBreakerForServices()
products_cb = CircitBreakerForServices()


@app.get("/main_api/ping")
def ping():
    return None

@app.get("/main_api/trigger_monitor")
def trigger_monitor():
    cba = CircuitBreakerMonitor.get_circuits()
    rst = ""
    for elm in cba:
        rst += f"{elm.state}\t{elm.failure_count}\t{elm.open_remaining if elm.opened else ''}\n"
    print(rst)
    return rst

# методы работы с пользователями
#===============================
@app.post("/main_api/user_create", tags=["User object methods"])
@users_cb
# добавить пользователя
async def user_create(  user_name : str = Body(...) ,
                        user_password : str = Body(...),
                        name_first : str = Body(None),
                        name_last : str = Body(None)
                        ):
    
    responce = requests.post("http://user_service:8000/mongo_api/user_create", 
                             json = {"user_name" : user_name, 
                                     "user_password" : user_password, 
                                     "name_first" : name_first, 
                                     "name_last" : name_last})
    return json.loads(responce.text)

@app.post("/main_api/authenticate_user", tags=["User object methods"])
@users_cb
async def authorise_user(user_name : str = Body(...) ,
                         user_password : str = Body(...)):

    
    responce = requests.post("http://user_service:8000/mongo_api/authenticate_user", 
                             json = {"user_name" : user_name, 
                                     "user_password" : user_password})
    return json.loads(responce.text)

@app.post("/main_api/user_change", tags=["User object methods"])
@users_cb
async def user_change(  token : str = Body(...),
                        user_name : str = Body(...),
                        user_password : str = Body(...),
                        name_first : str = Body(None),
                        name_last : str = Body(None)
                        ):
    
    responce = requests.post("http://user_service:8000/mongo_api/user_change", 
                             json = {"token" : token, 
                                     "user_name" : user_name, 
                                     "user_password" : user_password, 
                                     "name_first" : name_first, 
                                     "name_last" : name_last})
    return json.loads(responce.text)

# возвращаем данные по пользователю, пароль и имя которого предоставлено
@app.post("/main_api/produce_user_data", tags=["User object methods"])
@users_cb
async def produce_user_data(token : str = Body(...)):
    
    responce = requests.post("http://user_service:8000/mongo_api/produce_user_data", 
                             json = token)
    return json.loads(responce.text)

# возвращаем список всех корзин пользователя
@app.post("/main_api/produce_user_baskets", tags=["User object methods"])
@users_cb
async def produce_user_baskets( token : str = Body(...)):

    responce = requests.post("http://user_service:8000/mongo_api/produce_user_baskets", 
                             json = token)
    return json.loads(responce.text)

# возвращаем список всех корзин пользователя
@app.post("/main_api/find_user_data", tags=["User object methods"])
@users_cb
async def find_user_data(   user_name_mask : str = Body("") ,
                            name_first_mask : str = Body("") ,
                            name_last_mask : str = Body("")):

    responce = requests.post("http://user_service:8000/mongo_api/find_user_data", 
                             json = {"user_name_mask" : user_name_mask, 
                                     "name_first_mask" : name_first_mask,
                                     "name_last_mask" : name_last_mask})
    return json.loads(responce.text)

# методы работы с корзинами
#===============================
@app.post("/main_api/basket_create", tags=["Basket object methods"])
@baskets_cb
async def basket_create(token : str = Body(...)):
    
    responce = requests.post("http://basket_service:8000/mongo_api/basket_create", 
                             json = token)
    return json.loads(responce.text)

# общие данные о корзине
@app.post("/main_api/get_basket_data", tags=["Basket object methods"])
@baskets_cb
def get_basket_data(token : str = Body(...),
                    basket_id : str = Body(...)): 
    
    responce = requests.post("http://basket_service:8000/mongo_api/get_basket_data", 
                             json = {"token" : token,
                                     "basket_id" :  basket_id})
    return json.loads(responce.text)

# что лежит в коризне
@app.post("/main_api/get_basket_contents", tags=["Basket object methods"])
@baskets_cb
def get_products_in_basket(token : str = Body(...),
                           basket_id : str = Body(...)): 
    
    responce = requests.post("http://basket_service:8000/mongo_api/get_basket_contents", 
                             json = {"token" : token,
                                     "basket_id" :  basket_id})
    return json.loads(responce.text)

# добавить товар в корзину
@app.post("/main_api/basket_add_item", tags=["Basket object methods"])
@baskets_cb
async def basket_add_item(  token : str = Body(...) ,
                            basket_id : str = Body(...) ,
                            product_id : str = Body(...),
                            amount : int = Body(...)):
    
    responce = requests.post("http://basket_service:8000/mongo_api/basket_add_item", 
                             json = {"token" : token, 
                                     "basket_id" : basket_id, 
                                     "product_id" : product_id, 
                                     "amount" : amount})
    return json.loads(responce.text)

# поменять количество товара в корзине
@app.post("/main_api/basket_mod_item", tags=["Basket object methods"])
@baskets_cb
async def basket_mod_item(  token : str = Body(...) ,
                            basket_id : str = Body(...) ,
                            product_id : str = Body(...),
                            amount : int = Body(...)):
    
    responce = requests.post("http://basket_service:8000/mongo_api/basket_mod_item", 
                             json = {"token" : token, 
                                     "basket_id" : basket_id, 
                                     "product_id" : product_id, 
                                     "amount" : amount})
    return json.loads(responce.text)

# удалить товар из корзины
@app.post("/main_api/basket_remove_item", tags=["Basket object methods"])
@baskets_cb
async def basket_remove_item(   token : str = Body(...) ,
                                basket_id : str = Body(...) ,
                                product_id : str = Body(...)):
    
    responce = requests.post("http://basket_service:8000/mongo_api/basket_remove_item", 
                             json = {"token" : token, 
                                     "basket_id" : basket_id, 
                                     "product_id" : product_id})
    return json.loads(responce.text)

# закрыть коризину (тут в теории информация должна передаваться в сервис оплаты и доставки)
@app.post("/main_api/basket_finalize", tags=["Basket object methods"])
@baskets_cb
async def basket_finalize(  token : str = Body(...),
                            basket_id : str = Body(...)):
    
    
    responce = requests.post("http://basket_service:8000/mongo_api/basket_finalize", 
                             json = {"token" : token, 
                                     "basket_id" : basket_id})
    return json.loads(responce.text)


# методы работы с продуктами
#===============================
@app.post("/main_api/add_new_product", tags=["Product object methods"])
@products_cb
async def add_new_product(  product_name : str = Body(...),
                            product_price : int = Body(...),
                            product_amount : int = Body(...)):

    responce = requests.post("http://product_service:8000/mongo_api/add_new_product", 
                             json = {"product_name" : product_name, 
                                     "product_price" : product_price, 
                                     "product_amount" : product_amount})
    return json.loads(responce.text)

@app.get("/main_api/get_all_available_items_list", tags=["Product object methods"])
@products_cb
async def get_all_available_items_list():
    return json.loads(requests.get("http://product_service:8000/mongo_api/get_all_available_items_list").text)

@app.get("/mongo_api/get_product_data", tags=["Product object methods"])
@products_cb
async def get_product_data(product_id):
    return json.loads(requests.get(url = "http://product_service:8000/mongo_api/get_product_data", params = {"product_id" : product_id}).text)

@app.post("/main_api/change_product_data", tags=["Product object methods"])
@products_cb
async def add_new_product(  product_id : str = Body(...),
                            new_product_name : str = Body(None),
                            new_product_price : int = Body(None),
                            new_product_amount : int = Body(None)):
    
    responce = requests.post("http://product_service:8000/mongo_api/change_product_data", 
                             json = {"product_id" : product_id, 
                                     "new_product_name" : new_product_name, 
                                     "new_product_price" : new_product_price, 
                                     "new_product_amount" : new_product_amount})
    return json.loads(responce.text)
