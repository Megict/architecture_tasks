from fastapi import FastAPI
from fastapi import Request

from datetime import datetime
from datetime import timedelta
import psycopg2
import bcrypt


conn = psycopg2.connect(dbname='shop_db', user='mxcitn', password='1234')
cursor = conn.cursor()

app = FastAPI()

def verify_user(user_name, presented_password):
    try:
        cursor.execute(f"SELECT id, pword_hash, pword_salt FROM users WHERE username= '{user_name}';")
        user_id, user_password_hash, user_password_salt = cursor.fetchall()[0]
        if bcrypt.hashpw(presented_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
            return "OK", user_id
        else:
            return "WRONG PASSWORD"
    except IndexError:
        return "USER DOES NOT EXIST"


@app.get("/main_api/ping")
def ping():
    return None

# методы работы с пользователями
#===============================
@app.post("/main_api/user_create", tags=["User object methods"])
# добавить пользователя
async def user_create(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    name_first = request_details["name_first"] if "name_first" in request_details else 'Null'
    name_last = request_details["name_last"] if "name_last" in request_details else 'Null'
    
    # проверка, не занято ли имя
    cursor.execute(f"SELECT id FROM users WHERE username= '{user_name}';")
    if len(cursor.fetchall()) != 0:
        return "user name unavailable"
    # запись

    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')

    cursor.execute(f"INSERT INTO users (username, pword_hash, pword_salt, name_first, name_last)\
                        VALUES {user_name, password_hash, salt.decode('utf-8'), name_first, name_last};")
    conn.commit()
    return None

@app.post("/main_api/user_change", tags=["User object methods"])
async def user_change(request : Request):
    request_details = await request.json()
    # можно изменить что угодно, если данные не меняются, то надо передать старые
    old_user_name = request_details["old_user_name"]
    old_user_password = request_details["old_user_password"]

    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    name_first = request_details["name_first"] if "name_first" in request_details else 'Null'
    name_last = request_details["name_last"] if "name_last" in request_details else 'Null'

    # верификация по паролю
    cursor.execute(f"SELECT id, pword_hash, pword_salt FROM users WHERE username= '{old_user_name}';")
    user_id, user_password_hash, user_password_salt = cursor.fetchall()[0]
    if bcrypt.hashpw(old_user_password.encode('utf-8'), user_password_salt.encode('utf-8')).decode('utf-8') == user_password_hash:
        # проверка, не занято ли имя
        cursor.execute(f"SELECT id FROM users WHERE username= '{user_name}';")
        if len(cursor.fetchall()) != 0:
            return "user name unavailable"
        # запись
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(user_password.encode('utf-8'), salt).decode('utf-8')
        cursor.execute(f"UPDATE users SET username = '{user_name}', pword_hash = '{password_hash}', pword_salt = '{salt.decode('utf-8')}', name_first = '{name_first}', name_last = '{name_last}'\
                         WHERE id = {user_id};")
        conn.commit()
        return "OK"
    else:
        # неверный пароль, ничего не делаем
        return "WRONG PASSWORD"

@app.post("/main_api/user_initiate_session", tags=["User object methods"])
async def user_initiate_session(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    # возвращаем список всех корзин пользователя
    cursor.execute(f"SELECT * FROM baskets WHERE owner_user_id = {verify[1]}")
    return [{"basket id" : bask[0], "basket_owned" : bask[1], "basket_opened" : bask[2], "basket_closed" : bask[3], "basket_contents" : get_products_in_basket(bask[0], request)}  for bask in cursor.fetchall()]


@app.post("/main_api/find_user_data", tags=["User object methods", "Search"])
async def find_user_data(request : Request):
    request_details = await request.json()
    name_first_mask = request_details["name_first_mask"]
    name_last_mask = request_details["name_last_mask"]

    cursor.execute(f"SELECT * FROM users WHERE LOWER(name_first) LIKE '%{name_first_mask.lower()}%' AND LOWER(name_last) LIKE '%{name_last_mask.lower()}%';")

    return [{"user_name" : rec[1], "first_name" : rec[4], "last_name" : rec[5]} for rec in cursor.fetchall()]

# методы работы с корзинами
#===============================
@app.post("/main_api/basket_create", tags=["Basket object methods"])
async def basket_create(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    cursor.execute(f"INSERT INTO baskets (owner_user_id, time_opened)\
                        VALUES {verify[1], str(datetime.now())};")
    # смотрим id последней записи 
    cursor.execute("SELECT id FROM baskets ORDER BY id desc limit 1")
    basket_id = cursor.fetchall()[0][0]
    conn.commit()

    return basket_id

@app.get("/main_api/get_basket_contents", tags=["Basket object methods"])
def get_products_in_basket(basket_id, request : Request): 
    cursor.execute(f"SELECT product_id, name, price, product_amount FROM basket_to_product JOIN products ON product_id= products.id WHERE basket_id = {basket_id}")
    return [{"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]} for elm in cursor.fetchall()]

@app.post("/main_api/basket_add_item", tags=["Basket object methods"])
async def basket_add_item(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    product_id = request_details["product_id"]

    amount = request_details["amount"]
    # добавить проверку, что добавляемое количество меньше максимально доступного

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины

    cursor.execute(f"INSERT INTO basket_to_product (basket_id, product_id, product_amount)\
                        VALUES {basket_id, product_id, amount};")
    conn.commit()

    return "OK"

# поменять количество товара в корзине
@app.post("/main_api/basket_mod_item", tags=["Basket object methods"])
async def basket_mod_item(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    product_id = request_details["product_id"]

    amount = request_details["amount"]
    # добавить проверку, что добавляемое количество меньше максимально доступного

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины

    cursor.execute(f"UPDATE basket_to_product SET product_amount = {amount}\
                        WHERE basket_id= {basket_id} AND product_id= {product_id};")
    conn.commit()

    return "OK"

@app.post("/main_api/basket_remove_item", tags=["Basket object methods"])
async def basket_remove_item(request : Request):
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    product_id = request_details["product_id"]

    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    # доавить проверку принадлежности корзины

    cursor.execute(f"DELETE FROM basket_to_product\
                        WHERE basket_id= {basket_id} and product_id= {product_id};")
    conn.commit()

    return "OK"

@app.post("/main_api/basket_finalize", tags=["Basket object methods"])
async def basket_finalize(request : Request):
    # указываем дату закрытия корзины и возвращаем спиок всех товаров
    request_details = await request.json()
    user_name = request_details["user_name"]
    user_password = request_details["user_password"]
    
    basket_id = request_details["basket_id"]
    
    verify = verify_user(user_name, user_password)
    if verify[0] != "OK":
        return verify
    
    cursor.execute(f"UPDATE baskets SET time_colsed = '{str(datetime.now())}'\
                        WHERE id = {basket_id};")
    conn.commit()

    # сделать проверку, чтобы нельзя было закрыть одну и ту же корзину много раз
    cursor.execute(f"SELECT product_id, name, price, amount FROM basket_to_product JOIN products ON product_id= products.id WHERE basket_id = {basket_id}")
    return [{"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]} for elm in cursor.fetchall()]


# методы работы с продуктами
#===============================
@app.get("/main_api/get_all_available_items_list", tags=["Product object methods"])
async def get_all_available_items_list(request : Request):
    cursor.execute(f"SELECT * FROM products")
    return [{"id" : elm[0], "name" : elm[1], "price" : elm[2], "amount" : elm[3]} for elm in cursor.fetchall()]